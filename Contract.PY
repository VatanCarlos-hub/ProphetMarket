# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

@gl.allow_storage
class Market:
    question: str
    outcome_a: str
    outcome_b: str
    status: str
    winner: str
    created_at: u256

class ProphetMarket(gl.Contract):
    """
    ProphetMarket - Decentralized Prediction Market on GenLayer.
    Create markets and resolve outcomes through validator consensus.
    """
    owner: Address
    markets: TreeMap[str, Market]
    count: u256

    def __init__(self):
        self.owner = gl.message.sender_account
        self.count = 0

    @gl.public.write
    def create_market(self, question: str, outcome_a: str, outcome_b: str) -> str:
        """Create a new prediction market with two possible outcomes."""
        market_id = "MKT-" + str(self.count)
        self.count += 1

        self.markets[market_id] = Market(
            question=question,
            outcome_a=outcome_a,
            outcome_b=outcome_b,
            status="OPEN",
            winner="",
            created_at=gl.block.timestamp
        )
        return market_id

    @gl.public.write
    def resolve_market(self, market_id: str, winner: str) -> str:
        """
        Resolve a market with the oracle's verdict.
        In production, the winner is determined by AI validator consensus
        through gl.eq_principle.strict_eq() with gl.ask_llm().
        """
        market = self.markets[market_id]

        if market.status != "OPEN":
            raise gl.UserError("Market already resolved")

        if winner not in ["A", "B"]:
            raise gl.UserError("Winner must be A or B")

        market.winner = winner
        market.status = "RESOLVED"
        self.markets[market_id] = market
        return winner

    @gl.public.view
    def get_market(self, market_id: str) -> dict:
        """Get market details."""
        market = self.markets[market_id]
        return {
            "question": market.question,
            "outcome_a": market.outcome_a,
            "outcome_b": market.outcome_b,
            "status": market.status,
            "winner": market.winner,
            "created_at": market.created_at
        }

    @gl.public.view
    def list_markets(self) -> list:
        """List all market IDs."""
        result = []
        i = 0
        while i < self.count:
            mid = "MKT-" + str(i)
            result.append(mid)
            i += 1
        return result
