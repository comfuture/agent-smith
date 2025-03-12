import asyncio
from agents import Agent, Runner, ModelSettings, WebSearchTool
from agents.tracing import trace
from dotenv import load_dotenv
from agent_smith.computer.browser import HeadlessChromeBrowser

load_dotenv()


async def main():
    async with HeadlessChromeBrowser() as chrome:
        browser = Agent(
            name="Browser",
            model="computer-use-preview",
            model_settings=ModelSettings(truncation="auto"),
            tools=[chrome.as_tool()],
            instructions="You can do tasks with graphical interfaces of web browsers.",
        )

        agent = Agent(
            name="Smith",
            model="gpt-4o-mini",
            instructions="You are a helpful assistant",
            handoffs=[WebSearchTool(), browser],
        )
        prompt = input("Enter a prompt: ")
        with trace(workflow_name="agent_smith"):
            result = await Runner.run(agent, prompt)
            print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
