import classifyGenericModified as c

def test_zipcode_us_pattern():
    assert c._pattern_zipcode_us.search('SUNY DOWNSTATE MEDICAL CENTER, BROOKLYN, NY, 112032012')
    assert not c._pattern_zipcode_us.search('DEPT OF EDUCATION ARIZONA')
    assert c._pattern_zipcode_us.search('Keiser, City of, PO BOX 138, Keiser, AR, 723510138')

if __name__ == "__main__":
    test_zipcode_us_pattern()