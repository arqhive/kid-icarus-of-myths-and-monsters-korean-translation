"""Two-tile Hangul for dialogue: Galmuri7 initial+vowel on top, a drawn final below.

Galmuri7 squeezes finals into three pixel rows, so 을/술/일 read as 운/숱/잍 on
the Game Boy. Dialogue lines are spaced two tile rows apart instead, and the final
consonant gets its own tile directly under the syllable.
"""

# Final consonant index (0-27 in the Unicode syllable formula) -> rows of '#'.
# Patterns up to five columns are placed from x=1, wider ones from x=0.
FINALS = {
    1: ['#####', '....#', '....#', '....#'],                  # ㄱ
    2: ['##.###', '.#...#', '.#...#', '.#...#'],              # ㄲ
    3: ['####.#.', '...#.#.', '...##.#', '...#...'],          # ㄳ
    4: ['#....', '#....', '#....', '#####'],                  # ㄴ
    5: ['#..####', '#...#..', '#..#.#.', '####..#'],          # ㄵ
    6: ['#...###', '#....#.', '#...#.#', '####.#.'],          # ㄶ
    7: ['#####', '#....', '#....', '#####'],                  # ㄷ
    8: ['#####', '....#', '#####', '#....', '#####'],         # ㄹ
    9: ['###.###', '..#...#', '###...#', '#.....#', '###...#'],   # ㄺ
    10: ['###.###', '..#.#.#', '###.#.#', '#...###', '###....'],  # ㄻ
    11: ['###.#.#', '..#.###', '###.#.#', '#...###', '###....'],  # ㄼ
    12: ['###..#.', '..#..#.', '###.#.#', '#...#.#', '###....'],  # ㄽ
    13: ['###.###', '..#.#..', '###.###', '#...#..', '###.###'],  # ㄾ
    14: ['###.###', '..#..#.', '###..#.', '#...###', '###....'],  # ㄿ
    15: ['###..#.', '..#.###', '###..#.', '#...#.#', '###..#.'],  # ㅀ
    16: ['#####', '#...#', '#...#', '#####'],                 # ㅁ
    17: ['#...#', '#####', '#...#', '#####'],                 # ㅂ
    18: ['#.#..#.', '###..#.', '#.#.#.#', '###.#.#'],         # ㅄ
    19: ['..#..', '..#..', '.#.#.', '#...#'],                 # ㅅ
    20: ['.#..#.', '.#..#.', '#.##.#'],                       # ㅆ
    21: ['.###.', '#...#', '#...#', '.###.'],                 # ㅇ
    22: ['#####', '..#..', '.#.#.', '#...#'],                 # ㅈ
    23: ['..#..', '#####', '..#..', '.#.#.', '#...#'],        # ㅊ
    24: ['#####', '....#', '#####', '....#'],                 # ㅋ
    25: ['#####', '#....', '#####', '#....', '#####'],        # ㅌ
    26: ['#####', '.#.#.', '.#.#.', '#####'],                 # ㅍ
    27: ['..#..', '#####', '.###.', '#...#', '.###.'],        # ㅎ
}


def split(char):
    """Return (top character, final index or 0)."""
    if '가' <= char <= '힣':
        offset = ord(char) - 0xac00
        return chr(0xac00 + offset - offset % 28), offset % 28
    return char, 0


def final_rows(index):
    """Eight 1bpp rows for a final consonant tile."""
    pattern = FINALS[index]
    x0 = 1 if max(map(len, pattern)) <= 5 else 0
    rows = [0] * 8
    for y, line in enumerate(pattern):
        for x, c in enumerate(line):
            if c == '#':
                rows[y] |= 1 << (7 - x0 - x)
    return bytes(rows)
