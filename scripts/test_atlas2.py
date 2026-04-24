import unittest
import atlas2
import ipaddress
import pytest

class Atlas2Test(unittest.TestCase):

    def test_valid_domain(self):
        assert atlas2.is_valid_domain("pitt.k12.nc.us") == True

    def test_invalid_domain(self):
        assert atlas2.is_valid_domain("pittk12ncus") == False

    def test_valid_block(self):
        list = [ipaddress.ip_network('152.26.20.64/26'), ipaddress.ip_network('152.26.23.0/25')]
        self.assertListEqual(atlas2.is_valid_blocks("152.26.20.64/26, 152.26.23.0/25"), list)

    def test_invalid_block(self):
        with pytest.raises(SystemExit):
            assert atlas2.is_valid_blocks("") == "[!] No block given"

    def test_in_ip_block(self):
        block = [ipaddress.ip_network('152.26.20.64/26')]
        assert atlas2.ip_block_checker("152.26.20.64", block) == True

    def test_outside_ip_block(self):
        block = [ipaddress.ip_network('152.26.20.64/26')]
        assert atlas2.ip_block_checker("104.16.0.0", block) == False

    def test_get_domain_from_ip(self):
        domain_list = [
            ("example.com", ["1.1.1.1", "2.2.2.2"]),
            ("test.com", ["3.3.3.3", "1.1.1.1"]),
            ("other.com", ["4.4.4.4"])
        ]

        result = atlas2.get_domains_from_ip(domain_list, "1.1.1.1")

        assert set(result) == {"example.com", "test.com"}

if __name__ == "__main__":
    unittest.main()
