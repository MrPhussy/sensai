# Eliza Solana Example
*with Crossmint custodial wallets and GOAT*

This fork is a **simplified example of Eliza focused on executing transactions onchain** using Crossmint custodial wallets and [GOAT](https://github.com/goat-sdk/goat-sdk). It's designed specifically for Solana, focusing on agents that handle complex onchain tasks. By using GOAT for all onchain functionality, this version removes unnecessary plugins for other blockchains and introduces a simpler character to start with that is tailored to doing actions on Solana.

**Onchain actions**: Mint NFTs, check the latest trending tokens, purchase, trade them, and much more.

Tech stack:
- [Eliza](https://github.com/ai16z/eliza) - The AI agent framework
- [GOAT](https://github.com/goat-sdk/goat-sdk) - The open-source framework for connecting AI agents to any onchain app
- [Crossmint custodial wallets](https://docs.crossmint.com/wallets/introduction) - Best in class server-side MPC wallets

**Support**
- [Discord](https://discord.gg/goat-sdk)


## Running the project
### Requirements
- Node.js 23.3.0+

### Set up

1. Clone the repository
```bash
git clone https://github.com/goat-sdk/eliza-solana-example.git
```

2. Go into the project directory
```bash
cd eliza-solana-example
```

3. Install the dependencies
```bash
pnpm install
```

4. Run `pnpm build`

5. Copy the .env.example file to .env:
```bash
cp .env.example .env
```

6. Get an OpenAI API key and fill in the `OPENAI_API_KEY` in the .env file

### Giving the agent a wallet

1. Create a developer account in the Crossmint [Staging Console](https://staging.crossmint.com/console). Open that link, sign in, and accept the dialog to continue. *NOTE: Crossmint offers two consoles: staging, for development and testing, and www, for production.*

2. Once logged in, click the “Integrate” tab, then select “API Keys” from the top menu. Within the Server-side keys section, click the “Create new key” button in the top right. Then, select the scopes `wallets.create`, `wallets.read`, `wallets.fund`, `wallets:nfts.read`, `wallets:transactions.create` and `wallets:transactions.read` under the Wallets API category and create your key.

3. Save the key and fill in the following in the .env file:
    - `CROSSMINT_API_KEY=your_api_key`
    - `CROSSMINT_EMAIL=your_email@example.com`
    - `CROSSMINT_ENV=staging`

4. Create a wallet attached to the specified email by running the command `pnpm create-wallet`

### Running the agent

1. You can now run the agent with the command `pnpm start --character="characters/solana-hacker.character.json"`


## Configuring the project
### The character
- You can see the definition of your character in the `characters/solana-hacker.character.json` file.
- This project gives you a simple example character to get you started. This allows you to easily add onchain actions and test them out while increasing the complexity of your agent step by step. Keep adding and modifying the bio and tone of the character to make it your own.

### Eliza
- This is an Eliza fork so you can do pretty much everything you can do with Eliza. Check out the [Eliza docs](https://ai16z.github.io/eliza/) for more information on how to integrate your agent with Twitter, Discord, etc.

### Onchain actions with GOAT
- The Crossmint plugin (`packages/plugin-crossmint`) uses GOAT to add all onchain functionality to the agent. Within the `index.ts` file of the plugin you can add any GOAT plugins you need or even create your own. Check out the [GOAT docs](https://ohmygoat.dev) for more information.
```typescript
const actions = await getOnChainActions({
        wallet: walletClient,
        // Add plugins here based on what actions you want to use
        // See all available plugins at https://ohmygoat.dev/chains-wallets-plugins#plugins
        plugins: [
            // Add you solana plugins here
            splToken({
                connection,
                network: "mainnet",
            }),
            // coingecko({
            //  apiKey: getSetting("COINGECKO_API_KEY")
            // })
        ],
    });
```

## Tips for troubleshooting
1. When making changes to any package (e.g the Crossmint plugin), remember to run `pnpm build` to update the project.
2. To see why the agent is making a certain decision, add console logs to see the prompts and responses that it is getting on every interaction. For example. if you are using the direct client that would be [here](https://github.com/goat-sdk/eliza-solana-example/blob/main/packages/client-direct/src/index.ts#L135).
3. You can also copy the agent prompts that you log and play with them in ChatGPT to see how you could improve them.