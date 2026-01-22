"""
Wallet generation using BIP39/BIP44 standards.
Supports multiple blockchain networks.
"""

from typing import Optional

from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip39WordsNum,
    Bip44,
    Bip44Coins,
    Bip44Changes,
    Bip49,
    Bip49Coins,
    Bip84,
    Bip84Coins,
)

from .models import Chain, DerivationPath, WalletInfo


class WalletGenerator:
    """
    Generates cryptocurrency wallets from BIP39 mnemonics.
    Supports BIP44, BIP49, and BIP84 derivation paths.
    """
    
    # Mapping of chains to BIP44 coin types
    BIP44_COINS = {
        Chain.BITCOIN: Bip44Coins.BITCOIN,
        Chain.ETHEREUM: Bip44Coins.ETHEREUM,
        Chain.BNB: Bip44Coins.BINANCE_SMART_CHAIN,
        Chain.LITECOIN: Bip44Coins.LITECOIN,
        Chain.TRON: Bip44Coins.TRON,
    }
    
    BIP49_COINS = {
        Chain.BITCOIN: Bip49Coins.BITCOIN,
        Chain.LITECOIN: Bip49Coins.LITECOIN,
    }
    
    BIP84_COINS = {
        Chain.BITCOIN: Bip84Coins.BITCOIN,
        Chain.LITECOIN: Bip84Coins.LITECOIN,
    }
    
    def __init__(self, words_num: int = 12):
        """
        Initialize wallet generator.
        
        Args:
            words_num: Number of words in mnemonic (12, 15, 18, 21, or 24)
        """
        self.words_num = self._get_words_num(words_num)
    
    @staticmethod
    def _get_words_num(num: int) -> Bip39WordsNum:
        """Convert integer to Bip39WordsNum enum."""
        mapping = {
            12: Bip39WordsNum.WORDS_NUM_12,
            15: Bip39WordsNum.WORDS_NUM_15,
            18: Bip39WordsNum.WORDS_NUM_18,
            21: Bip39WordsNum.WORDS_NUM_21,
            24: Bip39WordsNum.WORDS_NUM_24,
        }
        if num not in mapping:
            raise ValueError(f"Invalid words number: {num}. Must be one of {list(mapping.keys())}")
        return mapping[num]
    
    def generate_mnemonic(self) -> str:
        """
        Generate a new BIP39 mnemonic phrase.
        
        Returns:
            A space-separated string of mnemonic words.
        """
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(self.words_num)
        return str(mnemonic)
    
    def derive_wallet(
        self,
        mnemonic: str,
        chain: Chain,
        derivation: DerivationPath = DerivationPath.BIP44,
        account: int = 0,
        address_index: int = 0,
    ) -> WalletInfo:
        """
        Derive a wallet address from a mnemonic.
        
        Args:
            mnemonic: BIP39 mnemonic phrase
            chain: Target blockchain
            derivation: Derivation path standard (BIP44/49/84)
            account: Account index
            address_index: Address index within account
            
        Returns:
            WalletInfo with derived address
        """
        try:
            seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
            
            if derivation == DerivationPath.BIP44:
                address, path = self._derive_bip44(
                    seed_bytes, chain, account, address_index
                )
            elif derivation == DerivationPath.BIP49:
                address, path = self._derive_bip49(
                    seed_bytes, chain, account, address_index
                )
            elif derivation == DerivationPath.BIP84:
                address, path = self._derive_bip84(
                    seed_bytes, chain, account, address_index
                )
            else:
                raise ValueError(f"Unsupported derivation path: {derivation}")
            
            return WalletInfo(
                chain=chain,
                address=address,
                derivation_path=path,
            )
            
        except Exception as e:
            return WalletInfo(
                chain=chain,
                address="",
                derivation_path=str(derivation),
                error=str(e),
            )
    
    def _derive_bip44(
        self,
        seed_bytes: bytes,
        chain: Chain,
        account: int,
        address_index: int,
    ) -> tuple[str, str]:
        """Derive address using BIP44 standard."""
        coin = self.BIP44_COINS.get(chain)
        if coin is None:
            raise ValueError(f"Chain {chain} not supported for BIP44")
        
        bip44_ctx = (
            Bip44.FromSeed(seed_bytes, coin)
            .Purpose()
            .Coin()
            .Account(account)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(address_index)
        )
        
        address = bip44_ctx.PublicKey().ToAddress()
        path = f"m/44'/{coin.CoinIndex()}'/{account}'/0/{address_index}"
        
        return address, path
    
    def _derive_bip49(
        self,
        seed_bytes: bytes,
        chain: Chain,
        account: int,
        address_index: int,
    ) -> tuple[str, str]:
        """Derive address using BIP49 standard (SegWit compatible)."""
        coin = self.BIP49_COINS.get(chain)
        if coin is None:
            raise ValueError(f"Chain {chain} not supported for BIP49")
        
        bip49_ctx = (
            Bip49.FromSeed(seed_bytes, coin)
            .Purpose()
            .Coin()
            .Account(account)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(address_index)
        )
        
        address = bip49_ctx.PublicKey().ToAddress()
        path = f"m/49'/{coin.CoinIndex()}'/{account}'/0/{address_index}"
        
        return address, path
    
    def _derive_bip84(
        self,
        seed_bytes: bytes,
        chain: Chain,
        account: int,
        address_index: int,
    ) -> tuple[str, str]:
        """Derive address using BIP84 standard (Native SegWit)."""
        coin = self.BIP84_COINS.get(chain)
        if coin is None:
            raise ValueError(f"Chain {chain} not supported for BIP84")
        
        bip84_ctx = (
            Bip84.FromSeed(seed_bytes, coin)
            .Purpose()
            .Coin()
            .Account(account)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(address_index)
        )
        
        address = bip84_ctx.PublicKey().ToAddress()
        path = f"m/84'/{coin.CoinIndex()}'/{account}'/0/{address_index}"
        
        return address, path
    
    def derive_all_wallets(
        self,
        mnemonic: str,
        chains: Optional[list[Chain]] = None,
        derivations: Optional[list[DerivationPath]] = None,
    ) -> list[WalletInfo]:
        """
        Derive wallets for multiple chains and derivation paths.
        
        Args:
            mnemonic: BIP39 mnemonic phrase
            chains: List of chains to derive (default: BTC, ETH)
            derivations: List of derivation paths (default: BIP44 only)
            
        Returns:
            List of WalletInfo for all combinations
        """
        if chains is None:
            chains = [Chain.BITCOIN, Chain.ETHEREUM]
        
        if derivations is None:
            derivations = [DerivationPath.BIP44]
        
        wallets = []
        for chain in chains:
            for derivation in derivations:
                # Skip unsupported combinations
                if derivation == DerivationPath.BIP49 and chain not in self.BIP49_COINS:
                    continue
                if derivation == DerivationPath.BIP84 and chain not in self.BIP84_COINS:
                    continue
                
                wallet = self.derive_wallet(mnemonic, chain, derivation)
                wallets.append(wallet)
        
        return wallets
