"""
Tests for data models.
"""

from src.wallet.models import WalletInfo, ScanResult, ScanStatistics, Chain


class TestWalletInfo:
    """Tests for WalletInfo dataclass."""
    
    def test_has_balance_true(self):
        """Test has_balance when balance > 0."""
        wallet = WalletInfo(
            chain=Chain.BITCOIN,
            address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            derivation_path="m/44'/0'/0'/0/0",
            balance=1.5,
            balance_checked=True,
        )
        assert wallet.has_balance is True
    
    def test_has_balance_false(self):
        """Test has_balance when balance = 0."""
        wallet = WalletInfo(
            chain=Chain.BITCOIN,
            address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            derivation_path="m/44'/0'/0'/0/0",
            balance=0,
            balance_checked=True,
        )
        assert wallet.has_balance is False
    
    def test_status_with_error(self):
        """Test status when there's an error."""
        wallet = WalletInfo(
            chain=Chain.ETHEREUM,
            address="0x123",
            derivation_path="m/44'/60'/0'/0/0",
            error="API timeout",
        )
        assert "Error" in wallet.status
    
    def test_status_pending(self):
        """Test status when not checked."""
        wallet = WalletInfo(
            chain=Chain.ETHEREUM,
            address="0x123",
            derivation_path="m/44'/60'/0'/0/0",
            balance_checked=False,
        )
        assert wallet.status == "Pending"


class TestScanResult:
    """Tests for ScanResult dataclass."""
    
    def test_has_any_balance(self):
        """Test has_any_balance property."""
        result = ScanResult(
            seed="test seed phrase here",
            wallets=[
                WalletInfo(Chain.BITCOIN, "addr1", "path1", balance=0),
                WalletInfo(Chain.ETHEREUM, "addr2", "path2", balance=1.0),
            ],
        )
        assert result.has_any_balance is True
    
    def test_no_balance(self):
        """Test has_any_balance when no wallets have balance."""
        result = ScanResult(
            seed="test seed phrase here",
            wallets=[
                WalletInfo(Chain.BITCOIN, "addr1", "path1", balance=0),
                WalletInfo(Chain.ETHEREUM, "addr2", "path2", balance=0),
            ],
        )
        assert result.has_any_balance is False
    
    def test_masked_seed(self):
        """Test seed masking for security."""
        result = ScanResult(
            seed="word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12",
            wallets=[],
        )
        masked = result.masked_seed
        assert "word1" in masked
        assert "word2" in masked
        assert "word11" in masked
        assert "word12" in masked
        assert "****" in masked
        assert "word5" not in masked
    
    def test_wallets_with_balance(self):
        """Test filtering wallets with balance."""
        result = ScanResult(
            seed="test",
            wallets=[
                WalletInfo(Chain.BITCOIN, "addr1", "path1", balance=0),
                WalletInfo(Chain.ETHEREUM, "addr2", "path2", balance=1.0),
                WalletInfo(Chain.BNB, "addr3", "path3", balance=0.5),
            ],
        )
        with_balance = result.wallets_with_balance
        assert len(with_balance) == 2
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = ScanResult(
            seed="test seed",
            wallets=[
                WalletInfo(Chain.BITCOIN, "addr1", "path1", balance=1.0),
            ],
        )
        data = result.to_dict()
        assert "seed" in data
        assert "wallets" in data
        assert len(data["wallets"]) == 1


class TestScanStatistics:
    """Tests for ScanStatistics dataclass."""
    
    def test_increment_counters(self):
        """Test counter increment methods."""
        stats = ScanStatistics()
        
        stats.increment_scanned()
        stats.increment_scanned()
        stats.increment_found()
        stats.increment_errors()
        
        assert stats.total_scanned == 2
        assert stats.wallets_found == 1
        assert stats.errors == 1
    
    def test_scan_rate(self):
        """Test scan rate calculation."""
        stats = ScanStatistics()
        stats.total_scanned = 100
        
        # Rate depends on elapsed time
        rate = stats.scan_rate
        assert rate >= 0
