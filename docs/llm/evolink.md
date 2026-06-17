## EvoLink

EvoLink extends the OpenAI LLM integration and uses EvoLink's OpenAI-compatible Chat Completions API.

Set `EVOLINK_API_KEY` to your EvoLink API key. The default API base is `https://direct.evolink.ai/v1`, and the default chat model is `gpt-5.2`.

### EvoLink Config

EvoLink Config is the configuration object for EvoLink. It is used to configure EvoLink and is passed to EvoLink when it is created.

::: director.llm.evolink.EvolinkConfig

### EvoLink Interface

EvoLink is the LLM used by the agents and tools. It is used to generate responses to messages.

::: director.llm.evolink.Evolink
