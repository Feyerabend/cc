
## LIBRIS Xsearch Interface

LIBRIS is the Swedish national library catalogue, maintained by the National Library of Sweden.
The Xsearch API provides public read access to the full catalogue and is described at:
* https://libris.kb.se/help/xsearch_eng.jsp?redirected=true&language=en

This folder contains three standalone HTML files -- each a self-contained browser application
that queries the LIBRIS Xsearch API and presents results in a different way. No server, build
step, or API key is required; open any file directly in a browser.


### libris.html -- Multi-format search

A general-purpose search interface that exposes the full range of output formats the Xsearch
API supports:

| Format | Notes |
|--------|-------|
| JSON | Parsed and displayed as structured result cards |
| BibTeX, Oxford, Harvard, RefWorks | Displayed as formatted citation blocks |
| MARC-XML, MODS | Parsed via `DOMParser`, displayed as structured cards with a raw XML toggle |
| RIS, Dublin Core, RDF + Dublin Core | Displayed as raw text |

Results are paginated (10 per page) with previous/next navigation. The format selector is
preserved across page turns, so you can browse a full BibTeX or MODS result set page by page.


### libris-bibtex.html -- Search with keyword recommendations

A focused JSON search interface that adds two features on top of basic retrieval:

1. *Search history* -- every query is saved to `localStorage` (up to 20 entries) and can be
   recalled from the history panel. Clicking a past query re-runs it immediately.

2. *Keyword recommendation engine* -- a small in-memory knowledge base accumulates the last
   50 fetched items across searches. For each new search the engine:
   - extracts keywords from titles and subjects (words longer than 3 characters, minus
     common stop words)
   - scores knowledge-base items by the number of keywords they share with the current
     first result
   - surfaces the top 3 matches as clickable recommendation cards

   Recommendations are computed *before* the current results are added to the knowledge base,
   so an item cannot recommend itself.

*Limitation:* keyword overlap is a weak similarity signal. Two books on the same topic may
share no title words at all and therefore score zero. The semantic version below addresses this.


### libris-semantic.html -- Search with semantic re-ranking

The same JSON search against the LIBRIS API, extended with in-browser neural embeddings. The
page loads a pre-trained sentence-transformer model (`all-MiniLM-L6-v2`, ~23 MB) via
Transformers.js, which compiles it to WebAssembly and runs it entirely client-side -- no data
leaves the browser.

The search pipeline has two stages:

1. *Keyword retrieval* -- the LIBRIS API returns up to 10 results for the query as usual.
   This stage is unchanged; the API does not support vector queries.

2. *Semantic re-ranking* -- the query and each result's title + subjects are independently
   embedded into 384-dimensional vectors. Results are then sorted by cosine similarity to
   the query vector and displayed with a similarity score and a proportional bar.

A knowledge base (up to 100 items) accumulates embedded results across searches. Recommendations
are drawn from *previous* searches by nearest-neighbour lookup in that store, so they can
surface related works from entirely different queries -- something keyword overlap cannot do.

*What the model does:* `all-MiniLM-L6-v2` is a distilled sentence-transformer trained on large
corpora of paraphrase pairs. It maps variable-length text to a fixed-size vector such that
semantically similar passages land close together in vector space, regardless of whether they
share any words. Cosine similarity of two pre-normalised vectors reduces to a dot product.

*Limitation:* re-ranking only reorders what the keyword search already returned. A semantically
relevant item that the keyword query did not retrieve will still be missed. True semantic search
over the full LIBRIS corpus would naturally require a vector index on the server side.


### Comparison

|   | libris.html | libris-bibtex.html | libris-semantic.html |
|---|-------------|--------------------|----------------------|
| Output formats | 10 | JSON only | JSON only |
| Pagination | yes | yes | yes |
| Search history | -- | localStorage | -- |
| Recommendations | -- | keyword overlap | vector similarity |
| Re-ranks results | -- | -- | yes |
| Requires network (model) | -- | -- | first load only |
