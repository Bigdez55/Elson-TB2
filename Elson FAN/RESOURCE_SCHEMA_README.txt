Schema overview

Files
from_doc_urls.csv and from_doc_urls.jsonl
  Every unique URL found in Elson Financial.docx, with its inferred title and a coarse type.
from_doc_books.csv
  Book like entries and titled works detected in the doc text.
from_doc_providers.csv
  Training or exam prep providers and similar vendor references detected in the doc text.
from_doc_standards_mentions.csv
  Standards and statutory frameworks mentioned in the doc text.
expansion_pack.csv and expansion_pack.jsonl
  Curated, high authority expansion pack to cover missing areas.
master_resources.csv and master_resources.jsonl
  Combined master list, doc plus expansion.

Fields
source
  doc or expansion

category
  Normalized category bucket, for example URLs, Books, Providers, Standards

resource_type
  URL, URL PDF, Journal or publisher page, Government or regulator, Course or training, Dataset or data, Standard or framework

domain and subdomain
  Expansion pack only, used for business topic grouping

jurisdiction
  Federal, State, Multi state, Global, or blank

notes
  Expansion pack only, short purpose or usage notes

contexts_count
  Doc only, number of times the URL appeared in the document
