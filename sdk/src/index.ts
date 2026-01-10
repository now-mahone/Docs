import { 
    createPublicClient, 
    createWalletClient, 
    http, 
    parseEther, 
    Address, 
    PublicClient, 
    WalletClient,
    getContract
} from 'viem';
import { base } from 'viem/chains';
import KerneVaultFactoryABI from './abis/KerneVaultFactory.json';
import KerneVaultABI from './abis/KerneVault.json';
import IERC20ABI from './abis/IERC20.json';

export class KerneSDK {
    public publicClient: PublicClient;
    public walletClient?: WalletClient;
    public factoryAddress: Address;

    constructor(factoryAddress: Address, rpcUrl: string, walletClient?: WalletClient) {
        this.factoryAddress = factoryAddress;
        this.publicClient = createPublicClient({
            chain: base,
            transport: http(rpcUrl)
        }) as PublicClient;
        this.walletClient = walletClient;
    }

    // --- Factory Methods ---

    async deployVault(params: {
        asset: Address;
        name: string;
        symbol: string;
        admin: Address;
        founder: Address;
        founderFeeBps: number;
        performanceFeeBps: number;
        whitelistEnabled: boolean;
        maxTotalAssets: bigint;
    }) {
        if (!this.walletClient || !this.walletClient.account) throw new Error("Wallet client required for deployment");

        const deploymentFee = await this.publicClient.readContract({
            address: this.factoryAddress,
            abi: KerneVaultFactoryABI.abi,
            functionName: 'deploymentFee',
        }) as bigint;

        const { request } = await this.publicClient.simulateContract({
            account: this.walletClient.account,
            address: this.factoryAddress,
            abi: KerneVaultFactoryABI.abi,
            functionName: 'deployVault',
            args: [
                params.asset,
                params.name,
                params.symbol,
                params.admin,
                params.founder,
                params.founderFeeBps,
                params.performanceFeeBps,
                params.whitelistEnabled,
                params.maxTotalAssets
            ],
            value: deploymentFee
        });

        return await this.walletClient.writeContract(request);
    }

    async getUserVaults(user: Address): Promise<Address[]> {
        return await this.publicClient.readContract({
            address: this.factoryAddress,
            abi: KerneVaultFactoryABI.abi,
            functionName: 'getUserVaults',
            args: [user]
        }) as Address[];
    }

    // --- Vault Methods ---

    async getVaultData(vaultAddress: Address) {
        const vault = getContract({
            address: vaultAddress,
            abi: KerneVaultABI.abi,
            client: this.publicClient
        });

        const [totalAssets, totalSupply, projectedAPY, symbol] = await Promise.all([
            vault.read.totalAssets(),
            vault.read.totalSupply(),
            vault.read.getProjectedAPY(),
            vault.read.symbol()
        ]);

        return {
            totalAssets,
            totalSupply,
            projectedAPY,
            symbol
        };
    }

    async deposit(vaultAddress: Address, amount: bigint, receiver: Address) {
        if (!this.walletClient || !this.walletClient.account) throw new Error("Wallet client required");

        const vault = getContract({
            address: vaultAddress,
            abi: KerneVaultABI.abi,
            client: { public: this.publicClient, wallet: this.walletClient }
        });

        const assetAddress = await vault.read.asset() as Address;
        
        // Check allowance
        const allowance = await this.publicClient.readContract({
            address: assetAddress,
            abi: IERC20ABI.abi,
            functionName: 'allowance',
            args: [this.walletClient.account.address, vaultAddress]
        }) as bigint;

        if (allowance < amount) {
            const { request: approveRequest } = await this.publicClient.simulateContract({
                account: this.walletClient.account,
                address: assetAddress,
                abi: IERC20ABI.abi,
                functionName: 'approve',
                args: [vaultAddress, amount]
            });
            await this.walletClient.writeContract(approveRequest);
        }

        const { request } = await this.publicClient.simulateContract({
            account: this.walletClient.account,
            address: vaultAddress,
            abi: KerneVaultABI.abi,
            functionName: 'deposit',
            args: [amount, receiver]
        });

        return await this.walletClient.writeContract(request);
    }
}
