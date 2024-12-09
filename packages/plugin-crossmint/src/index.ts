import type { Plugin } from "@ai16z/eliza";
import { getOnChainActions } from "./actions";
import { getWalletClient, getWalletProvider } from "./wallet";

async function createCrossmintPlugin(
    getSetting: (key: string) => string | undefined
): Promise<Plugin> {
    const walletClient = await getWalletClient(getSetting);
    if (!walletClient) {
        throw new Error("Wallet client not found");
    }
    console.log("walletClient", walletClient);
    const actions = await getOnChainActions({
        wallet: walletClient,
        // Add plugins here based on what actions you want to use
        // See all available plugins at https://ohmygoat.dev/chains-wallets-plugins#plugins
        plugins: [
            // Add you solana plugins here
        ],
    });

    return {
        name: "[Crossmint] Solana Onchain Actions",
        description: "Crossmint Solana integration plugin",
        providers: [getWalletProvider(walletClient)],
        evaluators: [],
        services: [],
        actions: actions,
    };
}

export default createCrossmintPlugin;
