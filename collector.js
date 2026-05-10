#!/usr/bin/env node
'use strict';

// ================================================================
// school-data-collector  —  collector.js
//
// Enriches TBD_CLC_School_Database.xlsx with Reddit, IPEDS, and
// Facebook/Google data, writing results to
// TBD_CLC_School_Database_enriched.xlsx.
//
// Usage:
//   GOOGLE_API_KEY=xxx GOOGLE_CSE_ID=yyy node collector.js
//
// Dependencies:
//   npm install xlsx axios cheerio
//
// Estimated runtime: ~60–90 min for 558 schools (due to API delays)
// Auto-saves every 50 schools in case of interruption.
// ================================================================

const XLSX = require('xlsx');
const axios = require('axios');
const fs = require('fs');
// cheerio available if HTML scraping needed: const cheerio = require('cheerio');

// ── Configuration ────────────────────────────────────────────────────
const INPUT_FILE  = 'TBD_CLC_School_Database.xlsx';
const OUTPUT_FILE = 'TBD_CLC_School_Database_enriched.xlsx';
const SHEET_NAME  = 'CLC School Database';

const GOOGLE_API_KEY = process.env.GOOGLE_API_KEY || '';
const GOOGLE_CSE_ID  = process.env.GOOGLE_CSE_ID  || '';

const REDDIT_UA  = 'Mozilla/5.0 (compatible; SchoolScorer/1.0)';
const SAVE_EVERY = 50; // auto-save interval (rows)

// ── Column order (A–X) ───────────────────────────────────────────────
const EXISTING_COLS = [
  'School Name',
  'State',
  'NCAA Division / Conference',
  'Mascot Name',
  'Historical Mascot Count',
  'Est. Student Population',
  'Est. Alumni Count',
  'Facebook Alumni Page URL',
  'Reddit Page URL',
  'Fight Song Link',
  'Fanatics Carries?',
  'Priority Tier',
  'Notes / HBCU / Target',
];

const NEW_COLS = [
  'Reddit Subscribers',          // N
  'Reddit Active Users',         // O
  'Reddit Activity Level',       // P
  'Reddit Score (1-5)',          // Q
  'Facebook Page Followers',     // R
  'Community Penetration Rate %',// S
  'Penetration Score (1-5)',     // T
  'IPEDS Enrollment',            // U
  'IPEDS Year',                  // V
  'Latitude',                    // W
  'Longitude',                   // X
];

const ALL_COLS = [...EXISTING_COLS, ...NEW_COLS];

// ── Utilities ────────────────────────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms));

function isBlank(val) {
  if (val === undefined || val === null) return true;
  const s = String(val).trim();
  return s === '' || s.toUpperCase() === 'AGENT_NEEDED' || s.toUpperCase().includes('AGENT_NEEDED');
}

function enc(str) {
  return encodeURIComponent(String(str || ''));
}

/**
 * Thin axios wrapper with retry on 429 / network error.
 */
async function httpGet(url, config = {}, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await axios.get(url, {
        timeout: 14000,
        validateStatus: () => true, // never throw on HTTP error status
        ...config,
      });
      // Back off and retry on rate-limit
      if (res.status === 429 && attempt < retries) {
        await sleep((attempt + 1) * 4000);
        continue;
      }
      return res;
    } catch (err) {
      if (attempt === retries) throw err;
      await sleep(2000);
    }
  }
}

// ════════════════════════════════════════════════════════════════════
// LAYER 1  —  Reddit
// ════════════════════════════════════════════════════════════════════

function redditActivityMap(subscribers) {
  if (!subscribers || subscribers < 100) return { level: 'No subreddit',      score: 1 };
  if (subscribers < 500)                 return { level: 'Barely exists',     score: 2 };
  if (subscribers < 2000)                return { level: 'Exists but quiet',  score: 3 };
  if (subscribers < 10000)               return { level: 'Active',            score: 4 };
  return                                        { level: 'Thriving',          score: 5 };
}

/**
 * Try the direct /about.json endpoint for a given subreddit name.
 * Returns null if the subreddit is not found or has no subscribers.
 */
async function redditAbout(name) {
  const url = `https://www.reddit.com/r/${encodeURIComponent(name)}/about.json`;
  const res = await httpGet(url, { headers: { 'User-Agent': REDDIT_UA } });
  if (res.status !== 200) return null;
  const d = res.data?.data;
  if (!d || !d.subscribers) return null;
  return {
    url:         `https://www.reddit.com${d.url || `/r/${d.display_name}/`}`,
    subscribers: d.subscribers     || 0,
    activeUsers: d.accounts_active || 0,
  };
}

/**
 * Subreddit search fallback.
 * Picks the result with the highest keyword overlap to the school name,
 * falling back to the first result if nothing clearly matches.
 */
async function redditSearch(schoolName) {
  const q   = enc(`${schoolName} university alumni`);
  const url = `https://www.reddit.com/search.json?q=${q}&type=sr&limit=5`;
  const res = await httpGet(url, { headers: { 'User-Agent': REDDIT_UA } });
  if (res.status !== 200) return null;

  const children = res.data?.data?.children || [];
  if (!children.length) return null;

  // Score results by keyword relevance
  const stopWords = new Set(['university', 'college', 'institute', 'of', 'the', 'and', 'at', 'for']);
  const keywords  = schoolName.toLowerCase().split(/\s+/).filter(w => w.length > 2 && !stopWords.has(w));

  let best = null, bestScore = -1;
  for (const { data: d } of children) {
    const corpus  = `${d.display_name} ${d.title} ${d.public_description}`.toLowerCase();
    const matches = keywords.filter(k => corpus.includes(k)).length;
    if (matches > bestScore || (matches === bestScore && d.subscribers > (best?.subscribers || 0))) {
      best      = d;
      bestScore = matches;
    }
  }

  if (!best) best = children[0]?.data;
  if (!best) return null;

  return {
    url:         `https://www.reddit.com${best.url || `/r/${best.display_name}/`}`,
    subscribers: best.subscribers     || 0,
    activeUsers: best.accounts_active || 0,
  };
}

/**
 * Full Reddit collection for one school.
 * Strategy: direct (original case) → direct (lowercase) → search fallback.
 * 1-second delay between every HTTP request per spec.
 */
async function collectReddit(schoolName) {
  const nameNoSpaces = schoolName.replace(/\s+/g, '');
  let result = null;

  // Attempt 1: direct URL, original casing
  try {
    result = await redditAbout(nameNoSpaces);
  } catch (_) { /* fall through */ }
  await sleep(1000);

  // Attempt 2: direct URL, all lowercase
  if (!result?.subscribers) {
    try {
      result = await redditAbout(nameNoSpaces.toLowerCase());
    } catch (_) { /* fall through */ }
    await sleep(1000);
  }

  // Attempt 3: search fallback
  if (!result?.subscribers) {
    try {
      result = await redditSearch(schoolName);
    } catch (e) {
      throw new Error(`Reddit search: ${e.message}`);
    }
  }

  if (!result?.subscribers) {
    return { found: false, url: '', subscribers: 0, activeUsers: 0, level: 'No subreddit', score: 1 };
  }

  const { level, score } = redditActivityMap(result.subscribers);
  return {
    found:       true,
    url:         result.url,
    subscribers: result.subscribers,
    activeUsers: result.activeUsers,
    level,
    score,
  };
}

// ════════════════════════════════════════════════════════════════════
// LAYER 2  —  NCES IPEDS via Urban Institute API
// ════════════════════════════════════════════════════════════════════

/**
 * Fetch enrollment, year, and coordinates from Urban Institute IPEDS.
 * Uses the most recent year with a non-zero enrollment.
 * 0.5-second delay is applied in the main loop after this call.
 */
async function collectIPEDS(schoolName) {
  const fields = 'inst_name,enrollment_fall_total,year,longitude,latitude';
  const url    = `https://educationdata.urban.org/api/v1/college-university/ipeds/directory/`
               + `?inst_name=${enc(schoolName)}&fields=${fields}`;

  const res = await httpGet(url);
  if (res.status !== 200 || !res.data?.results?.length) {
    return { found: false };
  }

  // Filter results with valid enrollment, sort newest-first
  const results = res.data.results
    .filter(r => r.enrollment_fall_total > 0)
    .sort((a, b) => (b.year || 0) - (a.year || 0));

  if (!results.length) return { found: false };

  // Prefer exact name match (case-insensitive), otherwise take first
  const nameLower  = schoolName.toLowerCase();
  const exactMatch = results.find(r => (r.inst_name || '').toLowerCase() === nameLower);
  const r          = exactMatch || results[0];

  return {
    found:      true,
    enrollment: r.enrollment_fall_total,
    year:       r.year,
    lat:        r.latitude  ?? '',
    lon:        r.longitude ?? '',
    alumni:     Math.round(r.enrollment_fall_total * 22),
  };
}

// ════════════════════════════════════════════════════════════════════
// LAYER 3  —  Google Custom Search → Facebook URL + Follower Count
// ════════════════════════════════════════════════════════════════════

let googleQuotaReached = false;

/**
 * Search Google CSE for a school's Facebook alumni page.
 * Parses follower count from the snippet if present.
 * Gracefully stops Layer 3 if daily quota is reached.
 */
async function collectFacebook(schoolName) {
  const empty = { found: false, url: 'Not found - manual check needed', followers: null };

  if (!GOOGLE_API_KEY || !GOOGLE_CSE_ID) return { ...empty, url: '' };
  if (googleQuotaReached) return empty;

  const q   = enc(`"${schoolName}" alumni association facebook`);
  const url = `https://www.googleapis.com/customsearch/v1`
            + `?key=${GOOGLE_API_KEY}&cx=${GOOGLE_CSE_ID}&q=${q}`;

  const res = await httpGet(url);

  // ── Quota / auth error detection ──────────────────────────────
  const httpStatus = res.status;
  const apiErr     = res.data?.error;
  const apiMsg     = (apiErr?.message || '').toLowerCase();
  const apiStatus  = apiErr?.status  || '';

  if (
    httpStatus === 429 ||
    apiStatus  === 'RESOURCE_EXHAUSTED' ||
    (httpStatus === 403 && (apiMsg.includes('quota') || apiMsg.includes('limit') || apiMsg.includes('exceeded')))
  ) {
    console.log('\n⚠  Daily quota reached — resume tomorrow or upgrade API plan\n');
    googleQuotaReached = true;
    return empty;
  }

  if (httpStatus !== 200 || !res.data?.items?.length) return empty;

  let facebookUrl   = '';
  let followerCount = null;

  for (const item of res.data.items) {
    if (item.link?.includes('facebook.com')) {
      if (!facebookUrl) facebookUrl = item.link;

      const snippet       = item.snippet || '';
      const followerMatch = snippet.match(/([0-9,]+)\s*followers/i);
      if (followerMatch) {
        followerCount = parseInt(followerMatch[1].replace(/,/g, ''), 10);
        if (facebookUrl) break; // have both — done
      }
    }
  }

  return {
    found:     !!facebookUrl,
    url:       facebookUrl || 'Not found - manual check needed',
    followers: followerCount,
  };
}

// ════════════════════════════════════════════════════════════════════
// OUTPUT SAVE
// ════════════════════════════════════════════════════════════════════

function saveOutput(rows) {
  const ws = XLSX.utils.json_to_sheet(rows, { header: ALL_COLS });
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, SHEET_NAME);
  XLSX.writeFile(wb, OUTPUT_FILE);
}

// ════════════════════════════════════════════════════════════════════
// MAIN
// ════════════════════════════════════════════════════════════════════

async function main() {
  // ── Load workbook ──────────────────────────────────────────────
  if (!fs.existsSync(INPUT_FILE)) {
    console.error(`\n❌  Input file not found: ${INPUT_FILE}`);
    console.error(`    Place ${INPUT_FILE} in the same directory as collector.js\n`);
    process.exit(1);
  }

  const wb = XLSX.readFile(INPUT_FILE);
  if (!wb.Sheets[SHEET_NAME]) {
    console.error(`\n❌  Sheet "${SHEET_NAME}" not found.`);
    console.error(`    Available sheets: ${wb.SheetNames.join(', ')}\n`);
    process.exit(1);
  }

  // ── Parse sheet with row 3 as headers (rows 1–2 are title/subtitle) ──
  const rawSheet = XLSX.utils.sheet_to_json(wb.Sheets[SHEET_NAME], {
    header: 1,
    defval: '',
  });
  const headers  = rawSheet[2];  // Row 3 (0-indexed = 2) holds column headers
  const dataRows = rawSheet.slice(3); // Data starts at row 4

  // Map each data row array to a keyed object
  const rows = dataRows.map(rowArr => {
    const obj = {};
    headers.forEach((h, i) => { obj[h] = rowArr[i] ?? ''; });
    return obj;
  });

  // Ensure every row has all new columns initialised (avoids undefined writes)
  rows.forEach(row => {
    NEW_COLS.forEach(col => { if (!(col in row)) row[col] = ''; });
  });

  // ── Count valid (processable) rows ────────────────────────────
  const validCount = rows.filter(r => {
    const n = String(r['School Name'] || '').trim();
    return n !== '' && !n.toUpperCase().includes('AGENT_NEEDED');
  }).length;

  const padLen = String(validCount).length;

  console.log(`\n📊  Loaded ${rows.length} rows  ·  ${validCount} processable schools`);
  console.log(`    Input:  ${INPUT_FILE}`);
  console.log(`    Output: ${OUTPUT_FILE}`);
  if (!GOOGLE_API_KEY) {
    console.log('\n⚠   GOOGLE_API_KEY not set — Layer 3 (Facebook) will be skipped');
    console.log('    Set env vars: GOOGLE_API_KEY=xxx GOOGLE_CSE_ID=yyy');
  }
  console.log('');

  // ── Counters ──────────────────────────────────────────────────
  const stats = { reddit: 0, facebook: 0, followers: 0, ipeds: 0, penetration: 0 };
  let processed = 0;

  // ── Process each row ──────────────────────────────────────────
  for (const row of rows) {
    const schoolName = String(row['School Name'] || '').trim();

    // Skip blank or placeholder rows
    if (!schoolName || schoolName.toUpperCase().includes('AGENT_NEEDED')) continue;

    processed++;
    const counter = `${String(processed).padStart(padLen, '0')}/${validCount}`;

    // Status indicators for progress line
    let redditStatus = '❌';
    let ipedsStatus  = '❌';
    let fbUrlStatus  = '❌';
    let fbFollowers  = '❌';

    // ── LAYER 1: Reddit ─────────────────────────────────────────
    let rData = {
      found: false, url: '', subscribers: 0,
      activeUsers: 0, level: 'No subreddit', score: 1,
    };

    try {
      rData = await collectReddit(schoolName);

      if (rData.found) {
        stats.reddit++;
        redditStatus = '✅';
        if (isBlank(row['Reddit Page URL'])) {
          row['Reddit Page URL'] = rData.url;
        }
      }
    } catch (e) {
      console.error(`  ⚠  Reddit error [${schoolName}]: ${e.message}`);
      if (isBlank(row['Reddit Page URL'])) row['Reddit Page URL'] = 'API Error';
    }

    row['Reddit Subscribers']    = rData.subscribers || '';
    row['Reddit Active Users']   = rData.activeUsers  || '';
    row['Reddit Activity Level'] = rData.level;
    row['Reddit Score (1-5)']    = rData.score;

    // ── LAYER 2: IPEDS ──────────────────────────────────────────
    let iData = { found: false };

    try {
      iData = await collectIPEDS(schoolName);
      await sleep(500); // 0.5s delay per spec

      if (iData.found) {
        stats.ipeds++;
        ipedsStatus = '✅';
        if (isBlank(row['Est. Student Population'])) row['Est. Student Population'] = iData.enrollment;
        if (isBlank(row['Est. Alumni Count']))       row['Est. Alumni Count']        = iData.alumni;
      }
    } catch (e) {
      console.error(`  ⚠  IPEDS error [${schoolName}]: ${e.message}`);
    }

    row['IPEDS Enrollment'] = iData.enrollment ?? '';
    row['IPEDS Year']       = iData.year       ?? '';
    row['Latitude']         = iData.lat        ?? '';
    row['Longitude']        = iData.lon        ?? '';

    // ── LAYER 3: Facebook ───────────────────────────────────────
    let fData = { found: false, url: 'Not found - manual check needed', followers: null };

    try {
      fData = await collectFacebook(schoolName);
      await sleep(1000); // 1s delay per spec

      if (fData.found) {
        stats.facebook++;
        fbUrlStatus = '✅';
        if (isBlank(row['Facebook Alumni Page URL'])) {
          row['Facebook Alumni Page URL'] = fData.url;
        }
      } else {
        // Write 'not found' message only if cell is still blank
        if (isBlank(row['Facebook Alumni Page URL'])) {
          row['Facebook Alumni Page URL'] = fData.url;
        }
      }

      if (fData.followers !== null) {
        stats.followers++;
        fbFollowers = fData.followers.toLocaleString();
      }
    } catch (e) {
      console.error(`  ⚠  Facebook error [${schoolName}]: ${e.message}`);
      if (isBlank(row['Facebook Alumni Page URL'])) row['Facebook Alumni Page URL'] = 'API Error';
    }

    row['Facebook Page Followers'] = fData.followers !== null ? fData.followers : '';

    // ── Penetration Rate ────────────────────────────────────────
    // Prefer Facebook followers, fall back to Reddit subscribers
    const communitySize = fData.followers || rData.subscribers || 0;
    const alumniCount   = parseInt(String(row['Est. Alumni Count']).replace(/,/g, ''), 10) || 0;

    if (communitySize > 0 && alumniCount > 0) {
      const penetrationRate = (communitySize / alumniCount) * 100;

      row['Community Penetration Rate %'] = Math.round(penetrationRate * 10) / 10;

      let penetrationScore;
      if      (penetrationRate >= 25) penetrationScore = 5;
      else if (penetrationRate >= 15) penetrationScore = 4;
      else if (penetrationRate >= 8)  penetrationScore = 3;
      else if (penetrationRate >= 3)  penetrationScore = 2;
      else                            penetrationScore = 1;

      row['Penetration Score (1-5)'] = penetrationScore;
      stats.penetration++;
    } else {
      row['Community Penetration Rate %'] = '';
      row['Penetration Score (1-5)']      = '';
    }

    // ── Progress log ────────────────────────────────────────────
    console.log(
      `[${counter}] ${schoolName}` +
      ` — Reddit: ${redditStatus}` +
      ` | IPEDS: ${ipedsStatus}` +
      ` | Facebook URL: ${fbUrlStatus}` +
      ` | FB Followers: ${fbFollowers}`
    );

    // ── Auto-save ───────────────────────────────────────────────
    if (processed % SAVE_EVERY === 0) {
      saveOutput(rows);
      console.log(`  💾  Auto-saved at school ${processed}/${validCount}`);
    }
  }

  // ── Final save ─────────────────────────────────────────────────
  saveOutput(rows);

  // ── Summary ─────────────────────────────────────────────────────
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('COLLECTION COMPLETE');
  console.log(`Reddit URLs found:             ${stats.reddit}/${validCount}`);
  console.log(`Facebook URLs found:           ${stats.facebook}/${validCount}`);
  console.log(`Facebook Followers found:      ${stats.followers}/${validCount}`);
  console.log(`IPEDS data found:              ${stats.ipeds}/${validCount}`);
  console.log(`Penetration rates calculated:  ${stats.penetration}/${validCount}`);
  console.log(`Output saved: ${OUTPUT_FILE}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
}

main().catch(err => {
  console.error('\n❌  Fatal error:', err.message);
  console.error(err.stack);
  process.exit(1);
});
