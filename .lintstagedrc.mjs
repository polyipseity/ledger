/**
 * @type {import('lint-staged').Configuration}
 */
export default {
  '**/*.{md,mdoc,mdown,mdx,mkd,mkdn,markdown,rmd}': ['pnpm run format:md'],
  '**/*.{astro,cjs,css,csv,gql,graphql,hbs,html,js,jsx,json,json5,jsonc,jsonl,less,mjs,pcss,sass,scss,svelte,styl,ts,tsx,vue,xml,yaml,yml}':
    ['pnpm run format:prettier'],
  '**/*.{py,pyi,pyw,pyx}': ['pnpm run format:py'],
  'ledger/[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]-[0-9][0-9]/**/*.journal': [
    'pnpm run format:journal',
  ],
};
