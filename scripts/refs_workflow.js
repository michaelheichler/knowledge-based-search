export const meta = {
  name: 'kbs-references-rebuild',
  description: 'Broad faithful summary of every chapter and section, one summarizer plus one validator per unit, website first then each book in order',
  phases: [
    { title: 'website', detail: 'exposingtheinvisible kit sections' },
    { title: 'osint-techniques', detail: 'OSINT Techniques (Bazzell, Edison)' },
    { title: 'osint-resources', detail: 'OSINT Resources (Bazzell)' },
    { title: 'digital-research-methods', detail: 'Handbook of Digital and Computational Research Methods' },
  ],
}

const REF_ROOT = '/Users/michael/dev/skills/knowledge-based-search/skills/knowledge-based-search/references'
const BUILD_ROOT = '/tmp/kbs_build'
const BASE = 'https://kit.exposingtheinvisible.org/en/'

const WEBSITE = [
  ['thekit', 'The Kit'], ['preamble', 'You are Already an Investigator'], ['safety', 'Safety First'],
  ['investigation-concepts', 'What Makes an Investigation'], ['evaluate-evidence', 'Evaluating Evidence and Information Sources'],
  ['fact-checking', 'The Basics of Fact-Checking'], ['navigating-libraries', 'Navigating Libraries and Archives'],
  ['collaboration', 'Investigation is Collaboration'], ['crowdsourcing', 'Crowdsourcing Evidence for Investigations'],
  ['osint-ocean', 'OSINT, Diving Into an Ocean of Information'], ['google-dorking', 'Search Smarter by Dorking'],
  ['web-archive', 'Retrieving and Archiving Information From Websites'], ['web', 'How to See What is Behind a Website'],
  ['maps', 'Using Maps to See Beyond the Obvious'], ['data-acquisition', 'Data Acquisition for Beginners'],
  ['geolocation', 'Geolocation Methods, a step by step guide'], ['field-research', 'Away From Your Screen, Out in the Field'],
  ['interviews', 'Interviews, the Human Element'], ['manage-sources', 'How to Manage Your Sources'],
  ['vulnerable-sources', 'How to Ethically Engage with Vulnerable Sources'], ['bio-investigation', 'Bio-investigations in the Field'],
  ['visual-evidence', 'Gathering Visual Evidence'], ['ocean-data', 'Ocean Datasets for Investigations'],
  ['supply-chain', 'Supply Chain and Product Investigations'], ['signs-symbols', 'Signs, Symbols and Other Visual Clues'],
  ['companies', 'What is in a Company'], ['critical-maps', 'Thinking Critically About Maps'],
  ['climate-change-adaptation', 'Investigating Climate Change Adaptation'], ['disinformation', 'How to Track Online Disinformation Networks'],
  ['world-story', 'The World Is a Story'], ['investigative-storytelling', 'Eight Breakable Rules of Investigative Writing'],
  ['anti-biometric', 'The Making of an Anti-biometric Mass Surveillance Campaign'], ['venmo', 'Extracting Information From Social Apps'],
  ['elections', 'Political Parties and Personal Data Brokers in the UK'], ['ad-watch', 'ad.watch, Investigating Political Ads'],
]

const BOOKS = [
  ['osint-techniques', 'OSINT Techniques (Bazzell, Edison, 11th ed.)', 57],
  ['osint-resources', 'Open Source Intelligence Techniques, Resources (Bazzell, 9th ed.)', 53],
  ['digital-research-methods', 'Handbook of Digital and Computational Research Methods (Madsen, Munk)', 26],
]

const SUMMARY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { written: { type: 'boolean' }, title: { type: 'string' }, path: { type: 'string' } },
  required: ['written', 'title', 'path'],
}

const VALIDATION_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { faithful: { type: 'boolean' }, complete: { type: 'boolean' }, fixed: { type: 'boolean' }, note: { type: 'string' } },
  required: ['faithful', 'complete', 'fixed', 'note'],
}

const STYLE = [
  'Cover the whole chapter: its main claims, the reasoning behind them, the methods or steps it describes, and the key facts, names, and terms a reader needs.',
  'Write from understanding, in plain language. Keep the core, drop illustration and repetition.',
  'Preserve concrete specifics exactly: names, figures, commands, defined terms.',
  'Stay faithful to the source. Add no claim, judgment, or framing that is not in the text.',
  'Let the chapter set the length. A dense chapter takes more, a thin one less.',
  'Punctuation: no em-dash or en-dash, no semicolon joining two clauses, no empty intensifiers. Use commas, periods, parentheses.',
].map((rule, i) => `${i + 1}. ${rule}`).join('\n')

function frontMatter(source) {
  return ['---', 'title: <a clear title for this chapter>', `source: ${source}`, '---'].join('\n')
}

function summarizePrompt(item) {
  const read = item.kind === 'web'
    ? `Fetch the page at ${item.url} with WebFetch. It is the section "${item.title}" from ${item.source}. If a cross-host redirect is returned, call WebFetch again with the redirect URL.`
    : `Read the text at ${item.path}. It is "${item.title}" from ${item.source}.`
  return [
    'Summarize one chapter for a reference library. Produce a general summary a reader can rely on without the original.',
    read,
    '',
    `Write the summary to ${item.outPath} as markdown, starting with this front matter (fill the angle-bracket field):`,
    frontMatter(item.source),
    'Then the summary. Write it this way:',
    STYLE,
    '',
    'Return the record (written, title, path).',
  ].join('\n')
}

function validatePrompt(item) {
  const read = item.kind === 'web' ? `fetch the page at ${item.url} with WebFetch` : `read the text at ${item.path}`
  return [
    'Validate one reference summary against its source.',
    `Source: ${read}.`,
    `Summary: read the file at ${item.outPath}.`,
    '',
    'Check two things:',
    '- Faithful: every claim in the summary is supported by the source, nothing invented.',
    '- Complete: the summary covers the chapter main content, not just part of it.',
    `If the summary fails either test, rewrite ${item.outPath} to fix it, keeping the same front matter and the broad plain style, and the same punctuation rules (no em-dash or en-dash, no semicolon joining clauses, no empty intensifiers).`,
    '',
    'Return the verdict (faithful, complete, fixed, note). Set fixed=true only if you rewrote the file.',
  ].join('\n')
}

function summarize(item) {
  return agent(summarizePrompt(item), { label: `sum:${item.id}`, phase: item.phase, model: 'sonnet', schema: SUMMARY_SCHEMA })
}

function validate(_prev, item) {
  return agent(validatePrompt(item), { label: `val:${item.id}`, phase: item.phase, model: 'sonnet', schema: VALIDATION_SCHEMA })
    .then((verdict) => ({ ...item, verdict }))
}

function unitIds(count) {
  return Array.from({ length: count }, (_, i) => `ch${String(i + 1).padStart(2, '0')}`)
}

const all = []

phase('website')
log(`website: ${WEBSITE.length} sections`)
const webItems = WEBSITE.map(([slug, title]) => ({
  kind: 'web', id: slug, title, source: 'Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)',
  url: BASE + slug + '.html', outPath: `${REF_ROOT}/exposingtheinvisible/${slug}.md`, phase: 'website',
}))
all.push(...(await pipeline(webItems, summarize, validate)))

for (const [slug, source, count] of BOOKS) {
  phase(slug)
  const items = unitIds(count).map((id) => ({
    kind: 'book', id, title: `unit ${id}`, source,
    path: `${BUILD_ROOT}/${slug}/${id}.txt`, outPath: `${REF_ROOT}/${slug}/${id}.md`, phase: slug,
  }))
  log(`${slug}: ${items.length} units (${source})`)
  all.push(...(await pipeline(items, summarize, validate)))
}

const done = all.filter(Boolean)
const unfaithful = done.filter((item) => item.verdict && !item.verdict.faithful)
const incomplete = done.filter((item) => item.verdict && !item.verdict.complete)
const fixed = done.filter((item) => item.verdict && item.verdict.fixed)
log(`done: ${done.length} units, ${fixed.length} fixed by validator, ${unfaithful.length} still unfaithful, ${incomplete.length} still incomplete`)
return {
  total: done.length,
  fixed: fixed.length,
  unfaithful: unfaithful.map((item) => item.outPath),
  incomplete: incomplete.map((item) => item.outPath),
}
