# ProphetMarket

A prediction market oracle on GenLayer. Anyone creates a two-outcome market with a public resolution source; GenLayer validators fetch that source independently and must agree on the result.

Contract source: ProphetMarketsContract.py (repo root)
Network: GenLayer Studio NEXT (chain id 61997)
Contract address: 0xb57C08DF3B263b340a372bf4c5b9F09a744a394D

## How it works

1. create_market(question, outcome_a, outcome_b, resolution_url, year)
   Stores a new market with id MKT-YYYY-NNNN and status OPEN. Inputs are validated deterministically (lengths, URL format, 4-digit year).

2. resolve_market(market_id)
   Every validator renders the resolution URL itself (gl.nondet.web.render) and asks its LLM to answer with exactly one token: A, B or UNDECIDED. The answer is normalized by a deterministic _pick() function, and validators must agree via gl.eq_principle.strict_eq.
   - A or B: market becomes RESOLVED with that winner.
   - UNDECIDED or unreachable source: market stays OPEN and can be retried later.

3. Views
   get_market(market_id), list_markets() (newest 50), market_count(), get_owner()

## Why consensus works

Validators run different LLMs, so free-form text would never match. The jury only returns a single token, and all bookkeeping (ids, counters, status, validation) is deterministic Python outside the non-deterministic block.

## Storage

Markets are stored as JSON strings in a TreeMap keyed by market id.
