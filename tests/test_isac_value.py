from isac import IsacNode, IsacValue

def test_creation():
    nA = IsacNode('A')
    nB = IsacNode('B')

    try:
        ivA = IsacValue(nA, 'my_value')
        ivB = IsacValue(nB, 'my_value')
    finally:
        nA.shutdown()
        nB.shutdown()
