from fframebuf.big_font import BigFont


font_56 = BigFont(width = 24) # 24 : space width

for digit in range(10):
    font_56.load_pbm(str(digit), f"/fonts/{digit}.pbm")
font_56.load_pbm('😀', "/fonts/😀.pbm")
font_56.load_pbm('🙁', "/fonts/🙁.pbm")
font_56.load_pbm('°', "/fonts/deg.pbm")
font_56.load_pbm('.', "/fonts/dot.pbm")