#!/usr/bin/env node
// ローカル限定のトークン使用量ビューア（git管理外 / 依存ゼロ）。
//
// claude CLI がセッションごとに ~/.claude/projects/<cwd>/<id>.jsonl に残す
// トランスクリプトを読み、各応答の usage を集計してターミナルに棒グラフで出す。
// MulmoClaude 本体には一切触れないので、CLI の実装が変わっても形式が同じなら動く。
//
// 使い方:
//   node scripts/local/usage-tui.mjs            # 直近7日
//   node scripts/local/usage-tui.mjs --days 30  # 期間指定
//   node scripts/local/usage-tui.mjs --all      # 全期間

import { readdirSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import path from "node:path";

const PROJECTS_DIR = path.join(homedir(), ".claude", "projects");
const BAR_WIDTH = 40;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

// ── 引数 ───────────────────────────────────────────────
function parseArgs(argv) {
  const all = argv.includes("--all");
  const di = argv.indexOf("--days");
  const days = di >= 0 ? Number(argv[di + 1]) : 7;
  return { all, days: Number.isFinite(days) && days > 0 ? days : 7 };
}

// ── ANSI ───────────────────────────────────────────────
const C = {
  reset: "\x1b[0m",
  dim: "\x1b[2m",
  bold: "\x1b[1m",
  cyan: "\x1b[36m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  gray: "\x1b[90m",
};

// cwd を人間向けラベルに。MulmoClaude 由来を強調する。
function labelFor(cwd) {
  if (!cwd) return { name: "(unknown)", kind: "other" };
  if (cwd.includes("workspace") && cwd.includes("mulmoclaude"))
    return { name: "MulmoClaude 開発 (このCLI)", kind: "dev" };
  if (cwd === "/home/node/mulmoclaude")
    return { name: "MulmoClaude アプリ (Docker)", kind: "app" };
  if (cwd.endsWith("/mulmoclaude"))
    return { name: "MulmoClaude アプリ", kind: "app" };
  // その他は末尾2セグメントで文脈を残す（basename だけだと "06" 等になり判別不能）。
  const parent = path.basename(path.dirname(cwd));
  const base = path.basename(cwd);
  const name = parent && base ? `${parent}/${base}` : base || cwd;
  return { name, kind: "other" };
}

const KIND_COLOR = { app: C.green, dev: C.cyan, other: C.gray };

// ── 集計 ───────────────────────────────────────────────
// usage 1件を「処理トークン総量」に畳む。runaway 検知には生の総量で十分。
function totalTokens(u) {
  return (
    (u.input_tokens || 0) +
    (u.cache_creation_input_tokens || 0) +
    (u.cache_read_input_tokens || 0) +
    (u.output_tokens || 0)
  );
}

function emptyAgg() {
  return { total: 0, input: 0, output: 0, cache: 0, msgs: 0 };
}

function addUsage(agg, u) {
  agg.total += totalTokens(u);
  agg.input += u.input_tokens || 0;
  agg.output += u.output_tokens || 0;
  agg.cache += (u.cache_read_input_tokens || 0) + (u.cache_creation_input_tokens || 0);
  agg.msgs += 1;
}

function localDate(ts) {
  const d = new Date(ts);
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

// 1行を処理して集計に反映。assistant かつ usage を持つ行のみ。
function ingestLine(line, cutoffMs, byProject, byDayApp) {
  let row;
  try {
    row = JSON.parse(line);
  } catch {
    return;
  }
  const u = row?.message?.usage;
  if (row?.type !== "assistant" || !u) return;
  const ms = Date.parse(row.timestamp);
  if (Number.isFinite(cutoffMs) && ms < cutoffMs) return;

  const { name, kind } = labelFor(row.cwd);
  const key = `${kind}:${name}`;
  if (!byProject.has(key)) byProject.set(key, { name, kind, ...emptyAgg() });
  addUsage(byProject.get(key), u);

  if (kind === "app") {
    const d = localDate(row.timestamp);
    if (!byDayApp.has(d)) byDayApp.set(d, emptyAgg());
    addUsage(byDayApp.get(d), u);
  }
}

function scanAll(cutoffMs) {
  const byProject = new Map();
  const byDayApp = new Map();
  let files = 0;
  let dirs;
  try {
    dirs = readdirSync(PROJECTS_DIR);
  } catch {
    return { byProject, byDayApp, files, missing: true };
  }
  for (const dir of dirs) {
    const full = path.join(PROJECTS_DIR, dir);
    let entries;
    try {
      entries = readdirSync(full);
    } catch {
      continue;
    }
    for (const fn of entries) {
      if (!fn.endsWith(".jsonl")) continue;
      const fp = path.join(full, fn);
      // 期間指定時、最終更新が cutoff より古いファイルは丸ごと飛ばす（高速化）。
      if (Number.isFinite(cutoffMs) && statSync(fp).mtimeMs < cutoffMs) continue;
      files += 1;
      const text = readFileSync(fp, "utf8");
      for (const line of text.split("\n")) {
        if (line) ingestLine(line, cutoffMs, byProject, byDayApp);
      }
    }
  }
  return { byProject, byDayApp, files, missing: false };
}

// ── 描画 ───────────────────────────────────────────────
function fmt(n) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}k`;
  return `${n}`;
}

const BLOCKS = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉"];

function bar(value, max, color) {
  const ratio = max > 0 ? value / max : 0;
  const units = ratio * BAR_WIDTH;
  let full = Math.floor(units);
  let rem = Math.round((units - full) * 8);
  // 端数が満タンに丸まったらブロック1つ繰り上げる（BLOCKS[8] は存在しないため）。
  if (rem >= 8) {
    full += 1;
    rem = 0;
  }
  const body = "█".repeat(full) + (rem > 0 ? BLOCKS[rem] : "");
  return `${color}${body || "·"}${C.reset}`;
}

// 全角（CJK・かな・全角記号）は表示上2カラム。.length は1なのでズレる。
function displayWidth(str) {
  let w = 0;
  for (const ch of str) {
    const c = ch.codePointAt(0);
    const wide =
      (c >= 0x1100 && c <= 0x115f) ||
      (c >= 0x2e80 && c <= 0xa4cf) ||
      (c >= 0xac00 && c <= 0xd7a3) ||
      (c >= 0xf900 && c <= 0xfaff) ||
      (c >= 0xff00 && c <= 0xff60) ||
      (c >= 0xffe0 && c <= 0xffe6);
    w += wide ? 2 : 1;
  }
  return w;
}

// 表示幅ベースで右詰めパディング（はみ出す場合は幅で切り詰め）。
function padDisplay(str, width) {
  let out = "";
  let w = 0;
  for (const ch of str) {
    const cw = displayWidth(ch);
    if (w + cw > width) break;
    out += ch;
    w += cw;
  }
  return out + " ".repeat(Math.max(0, width - w));
}

function printBars(rows, max) {
  const labelW = Math.min(28, Math.max(...rows.map((r) => displayWidth(r.label))));
  for (const r of rows) {
    const label = padDisplay(r.label, labelW);
    const color = r.color || C.green;
    const detail = r.detail ? ` ${C.dim}${r.detail}${C.reset}` : "";
    console.log(`  ${label} │ ${bar(r.value, max, color)} ${fmt(r.value)}${detail}`);
  }
}

function renderProjects(byProject) {
  const rows = [...byProject.values()].sort((a, b) => b.total - a.total);
  if (!rows.length) return;
  const max = rows[0].total;
  console.log(`\n${C.bold}プロジェクト別トークン消費${C.reset} ${C.dim}(MulmoClaude vs その他の切り分け)${C.reset}`);
  printBars(
    rows.map((r) => ({
      label: r.name,
      value: r.total,
      color: KIND_COLOR[r.kind],
      detail: `out ${fmt(r.output)} / ${r.msgs}msg`,
    })),
    max,
  );
}

function renderDaily(byDayApp) {
  const days = [...byDayApp.keys()].sort();
  if (!days.length) return;
  const rows = days.map((d) => ({ label: d, ...byDayApp.get(d) }));
  const max = Math.max(...rows.map((r) => r.total));
  console.log(`\n${C.bold}MulmoClaude アプリ 日別${C.reset} ${C.dim}(急増=暴走の兆候)${C.reset}`);
  const avg = rows.reduce((s, r) => s + r.total, 0) / rows.length;
  printBars(
    rows.map((r) => ({
      label: r.label,
      value: r.total,
      color: r.total > avg * 2 ? C.red : r.total > avg ? C.yellow : C.green,
      detail: `out ${fmt(r.output)} / ${r.msgs}msg`,
    })),
    max,
  );
  console.log(`  ${C.dim}赤=平均の2倍超 / 黄=平均超${C.reset}`);
}

function renderSummary(byProject, window) {
  const totals = [...byProject.values()].reduce(
    (s, r) => ({ total: s.total + r.total, output: s.output + r.output, msgs: s.msgs + r.msgs }),
    { total: 0, output: 0, msgs: 0 },
  );
  const app = [...byProject.values()]
    .filter((r) => r.kind === "app")
    .reduce((s, r) => s + r.total, 0);
  const share = totals.total > 0 ? ((app / totals.total) * 100).toFixed(0) : 0;
  console.log(`${C.bold}トークン使用量${C.reset} ${C.dim}(${window})${C.reset}`);
  console.log(
    `  総処理 ${C.bold}${fmt(totals.total)}${C.reset} tok / 出力 ${fmt(totals.output)} / ${totals.msgs} 応答`,
  );
  console.log(`  うち MulmoClaude アプリ: ${C.green}${fmt(app)} tok (${share}%)${C.reset}`);
}

// ── main ───────────────────────────────────────────────
function main() {
  const { all, days } = parseArgs(process.argv.slice(2));
  const cutoffMs = all ? NaN : Date.now() - days * ONE_DAY_MS;
  const window = all ? "全期間" : `直近${days}日`;

  const { byProject, byDayApp, files, missing } = scanAll(cutoffMs);
  if (missing) {
    console.error(`${C.red}~/.claude/projects が見つかりません${C.reset}`);
    process.exit(1);
  }
  if (!byProject.size) {
    console.log(`${window}に usage 付きのトランスクリプトがありません (走査 ${files} ファイル)`);
    return;
  }
  console.log("");
  renderSummary(byProject, window);
  renderProjects(byProject);
  renderDaily(byDayApp);
  console.log(`\n${C.dim}走査 ${files} ファイル · 処理トークン = 入力+キャッシュ+出力の総量${C.reset}\n`);
}

main();
