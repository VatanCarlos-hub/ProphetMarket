# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }

# ProphetMarket - a prediction market resolved by GenLayer validator consensus.
#
# 1. Anyone creates a market: a yes/no-style question with two outcomes (A, B)
#    and a public resolution source URL.
# 2. Anyone can trigger resolution. Every validator fetches the source itself,
#    and the jury answers with exactly ONE token: A, B or UNDECIDED.
#    gl.eq_principle.strict_eq compares that single token across validators.
# 3. A or B -> market is RESOLVED with that winner.
#    UNDECIDED (source does not settle it yet) -> market stays OPEN, retry later.
#
# All bookkeeping (ids, counters, validation) is deterministic Python outside
# the non-deterministic block. Records are stored as JSON strings.

import json
import genlayer as gl
from genlayer.types import *


OUTCOMES = ("A", "B")
UNDECIDED = "UNDECIDED"
UNREACHABLE = "UNREACHABLE"
MAX_SOURCE_CHARS = 8000
MAX_URL_CHARS = 500
LIST_LIMIT = 50


def _pick(raw) -> str:
    # Normalize a free-form LLM answer to A / B / UNDECIDED (deterministic fallback).
    text = str(raw).upper()
    cleaned = "".join(c if ("A" <= c <= "Z") else " " for c in text)
    for token in cleaned.split():
        if token in OUTCOMES or token == UNDECIDED:
            return token
    return UNDECIDED


def _check_len(value: str, lo: int, hi: int, label: str):
    if len(value) < lo or len(value) > hi:
        raise Exception(label + " must be " + str(lo) + "-" + str(hi) + " characters")


def _check_url(url: str):
    if not (url.startswith("https://") or url.startswith("http://")):
        raise Exception("resolution_url must start with https:// or http://")
    if len(url) > MAX_URL_CHARS or " " in url:
        raise Exception("resolution_url is invalid")


def _check_year(year: str):
    if len(year) != 4 or not year.isdigit():
        raise Exception("year must be 4 digits")


class ProphetMarket(gl.contract.Contract):
    markets: gl.storage.TreeMap[str, str]   # market_id -> record JSON
    owner: str
    market_seq: str

    def __init__(self):
        self.owner = str(gl.message.sender_address)
        self.market_seq = "0"

    # ---- write --------------------------------------------------------------

    @gl.public.write
    def create_market(
        self,
        question: str,
        outcome_a: str,
        outcome_b: str,
        resolution_url: str,
        year: str,
    ) -> str:
        question = question.strip()
        outcome_a = outcome_a.strip()
        outcome_b = outcome_b.strip()
        resolution_url = resolution_url.strip()
        year = year.strip()

        _check_len(question, 10, 300, "question")
        _check_len(outcome_a, 1, 80, "outcome_a")
        _check_len(outcome_b, 1, 80, "outcome_b")
        if outcome_a.lower() == outcome_b.lower():
            raise Exception("outcomes must differ")
        _check_url(resolution_url)
        # Year is passed in by the client: a contract has no consensus-safe clock.
        _check_year(year)

        n = int(self.market_seq) + 1
        self.market_seq = str(n)
        market_id = "MKT-" + year + "-" + str(n).zfill(4)
        record = {
            "id": market_id,
            "seq": n,
            "question": question,
            "outcome_a": outcome_a,
            "outcome_b": outcome_b,
            "resolution_url": resolution_url,
            "status": "OPEN",
            "winner": "",
            "attempts": 0,
            "created_by": str(gl.message.sender_address),
            "resolved_by": "",
        }
        self.markets[market_id] = json.dumps(record, sort_keys=True)
        return market_id

    @gl.public.write
    def resolve_market(self, market_id: str) -> str:
        market_id = market_id.strip()
        if market_id not in self.markets:
            raise Exception("market not found")
        record = json.loads(self.markets[market_id])
        if record["status"] != "OPEN":
            raise Exception("market already resolved")

        question = record["question"]
        outcome_a = record["outcome_a"]
        outcome_b = record["outcome_b"]
        url = record["resolution_url"]

        def judge() -> str:
            try:
                page = gl.nondet.web.render(url, mode="text")
            except Exception:
                return UNREACHABLE
            source = str(page or "").strip()[:MAX_SOURCE_CHARS]
            if len(source) < 20:
                return UNREACHABLE
            prompt = (
                "You resolve a prediction market using ONLY the source text below.\n"
                "Question: " + question + "\n"
                "Outcome A: " + outcome_a + "\n"
                "Outcome B: " + outcome_b + "\n\n"
                "Rules, apply in order:\n"
                "1. If the source clearly shows outcome A happened -> A\n"
                "2. If the source clearly shows outcome B happened -> B\n"
                "3. Otherwise (not yet decided, unclear, or not covered) -> UNDECIDED\n\n"
                "Answer with exactly one word: A, B or UNDECIDED.\n\n"
                "SOURCE:\n" + source
            )
            return _pick(gl.nondet.exec_prompt(prompt))

        verdict = gl.eq_principle.strict_eq(judge)

        record["attempts"] = int(record.get("attempts", 0)) + 1
        if verdict in OUTCOMES:
            record["status"] = "RESOLVED"
            record["winner"] = verdict
            record["resolved_by"] = str(gl.message.sender_address)
        self.markets[market_id] = json.dumps(record, sort_keys=True)
        return verdict

    # ---- views --------------------------------------------------------------

    @gl.public.view
    def get_market(self, market_id: str) -> str:
        market_id = market_id.strip()
        if market_id in self.markets:
            return self.markets[market_id]
        return json.dumps({"error": "not_found", "id": market_id})

    @gl.public.view
    def list_markets(self) -> str:
        # Newest first, up to LIST_LIMIT records.
        out = []
        for _, value in self.markets.items():
            out.append(json.loads(value))
        out.sort(key=lambda r: r.get("seq", 0), reverse=True)
        return json.dumps(out[:LIST_LIMIT])

    @gl.public.view
    def market_count(self) -> int:
        return int(self.market_seq)

    @gl.public.view
    def get_owner(self) -> str:
        return self.owner
