"""
Tests for wallet generation module.
"""

import pytest
from src.wallet import WalletGenerator, Chain, DerivationPath


class TestWalletGenerator:
    """Tests for WalletGenerator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.generator = WalletGenerator(words_num=12)
    
    def test_generate_mnemonic_12_words(self):
        """Test that mnemonic has 12 words."""
        mnemonic = self.generator.generate_mnemonic()
        words = mnemonic.split()
        assert len(words) == 12
    
    def test_generate_mnemonic_uniqueness(self):
        """Test that each generated mnemonic is unique."""
        mnemonics = [self.generator.generate_mnemonic() for _ in range(10)]
        assert len(set(mnemonics)) == 10
    
    def test_derive_bitcoin_wallet(self):
        """Test Bitcoin wallet derivation."""
        mnemonic = self.generator.generate_mnemonic()
        wallet = self.generator.derive_wallet(
            mnemonic=mnemonic,
            chain=Chain.BITCOIN,
            derivation=DerivationPath.BIP44,
        )
        
        assert wallet.chain == Chain.BITCOIN
        assert wallet.address != ""
        assert wallet.error is None
        assert "m/44'" in wallet.derivation_path
    
    def test_derive_ethereum_wallet(self):
        """Test Ethereum wallet derivation."""
        mnemonic = self.generator.generate_mnemonic()
        wallet = self.generator.derive_wallet(
            mnemonic=mnemonic,
            chain=Chain.ETHEREUM,
            derivation=DerivationPath.BIP44,
        )
        
        assert wallet.chain == Chain.ETHEREUM
        assert wallet.address.startswith("0x")
        assert wallet.error is None
    
    def test_derive_all_wallets(self):
        """Test deriving wallets for multiple chains."""
        mnemonic = self.generator.generate_mnemonic()
        wallets = self.generator.derive_all_wallets(
            mnemonic=mnemonic,
            chains=[Chain.BITCOIN, Chain.ETHEREUM],
            derivations=[DerivationPath.BIP44],
        )
        
        assert len(wallets) == 2
        chains = [w.chain for w in wallets]
        assert Chain.BITCOIN in chains
        assert Chain.ETHEREUM in chains
    
    def test_deterministic_derivation(self):
        """Test that same mnemonic produces same addresses."""
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        
        wallet1 = self.generator.derive_wallet(
            mnemonic=mnemonic,
            chain=Chain.ETHEREUM,
        )
        wallet2 = self.generator.derive_wallet(
            mnemonic=mnemonic,
            chain=Chain.ETHEREUM,
        )
        
        assert wallet1.address == wallet2.address
    
    def test_invalid_words_num(self):
        """Test that invalid words number raises error."""
        with pytest.raises(ValueError):
            WalletGenerator(words_num=13)


class TestChainEnum:
    """Tests for Chain enum."""
    
    def test_chain_symbols(self):
        """Test chain symbol properties."""
        assert Chain.BITCOIN.symbol == "BTC"
        assert Chain.ETHEREUM.symbol == "ETH"
        assert Chain.BNB.symbol == "BNB"
    
    def test_chain_string_representation(self):
        """Test chain string representation."""
        assert Chain.BITCOIN.value == "bitcoin"
        assert Chain.ETHEREUM.value == "ethereum"
