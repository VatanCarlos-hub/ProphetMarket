# ProphetMarket

A decentralized prediction market built on GenLayer. Create markets, let AI validator juries resolve outcomes through consensus, and build a new kind of oracle for real-world events.

## What is ProphetMarket?

ProphetMarket is an intelligent contract that enables anyone to create prediction markets with two possible outcomes. The resolution is powered by GenLayer's AI validator consensus - multiple independent LLMs research the question and must agree on a single-token answer before the market resolves.

## How it works

1. **Create a Market** - Anyone can create a market with a question and two outcomes (A/B)
2. **Place Bets** - Users bet on which outcome they believe will occur
3. **AI Oracle Resolution** - When the resolution time arrives, GenLayer's validator jury researches the real-world outcome using `gl.ask_llm()` and reaches consensus through `gl.eq_principle.strict_eq()`
4. **Market Settles** - The winning outcome is recorded on-chain

## The Oracle Pattern

```python
# AI Validator Consensus - Single-token agreement for reliability
result = gl.eq_principle.strict_eq(
    lambda: gl.ask_llm(
        "You are a prediction market oracle... Answer A or B only.",
        market.question
    )
)
Contract Methods
write
create_market(question, outco
