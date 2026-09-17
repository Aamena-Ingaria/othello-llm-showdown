BLACK = 1
WHITE = -1
EMPTY = 0

# Backwards compatibility
RED = BLACK
YELLOW = WHITE


def to_svg(board) -> str:
    """
    Create a stunning SVG representation of the 8x8 Othello board,
    featuring rich 3D discs, wooden border, green felt surface,
    star points, coordinate labels, and animations for the latest move.
    """
    # Dimensions
    board_size = 440
    offset_x = 40
    offset_y = 40
    cell_size = board_size / 8  # 55px per cell
    disc_radius = 22

    svg = f'''
    <div style="display: flex; justify-content: center; align-items: center; padding: 8px;">
    <svg width="500" height="500" viewBox="0 0 520 520" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto; filter: drop-shadow(0 10px 20px rgba(0,0,0,0.35));">
        <defs>
            <!-- Wood frame gradient -->
            <linearGradient id="frameGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#3d2314"/>
                <stop offset="50%" stop-color="#2a180d"/>
                <stop offset="100%" stop-color="#190e08"/>
            </linearGradient>

            <!-- Green felt gradient -->
            <radialGradient id="feltGradient" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#1b7a43"/>
                <stop offset="70%" stop-color="#145e33"/>
                <stop offset="100%" stop-color="#0e4424"/>
            </radialGradient>

            <!-- Black disc gradient (3D sphere effect) -->
            <radialGradient id="blackDisc" cx="35%" cy="32%" r="68%">
                <stop offset="0%" stop-color="#52525b"/>
                <stop offset="25%" stop-color="#27272a"/>
                <stop offset="75%" stop-color="#09090b"/>
                <stop offset="100%" stop-color="#000000"/>
            </radialGradient>

            <!-- White disc gradient (Pearl 3D effect) -->
            <radialGradient id="whiteDisc" cx="35%" cy="32%" r="68%">
                <stop offset="0%" stop-color="#ffffff"/>
                <stop offset="55%" stop-color="#f1f5f9"/>
                <stop offset="85%" stop-color="#cbd5e1"/>
                <stop offset="100%" stop-color="#94a3b8"/>
            </radialGradient>

            <!-- Shadow filter for pieces -->
            <filter id="pieceShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="2" dy="3" stdDeviation="2.5" flood-color="#000000" flood-opacity="0.55"/>
            </filter>

            <!-- Golden pulse glow for latest move -->
            <filter id="goldGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feComposite in="SourceGraphic" in2="blur" operator="over"/>
            </filter>
        </defs>

        <!-- Outer Wooden Border -->
        <rect x="8" y="8" width="504" height="504" rx="16" fill="url(#frameGradient)" stroke="#52311c" stroke-width="3"/>
        <rect x="24" y="24" width="472" height="472" rx="8" fill="none" stroke="#150b05" stroke-width="2"/>

        <!-- Green Felt Playing Surface -->
        <rect x="{offset_x}" y="{offset_y}" width="{board_size}" height="{board_size}" rx="4" fill="url(#feltGradient)" stroke="#092e18" stroke-width="2"/>
    '''

    # Grid Lines
    cols_str = "ABCDEFGH"
    for i in range(9):
        pos = offset_x + i * cell_size
        # Vertical lines
        svg += f'<line x1="{pos}" y1="{offset_y}" x2="{pos}" y2="{offset_y + board_size}" stroke="#0b381d" stroke-width="1.5"/>\n'
        # Horizontal lines
        pos_y = offset_y + i * cell_size
        svg += f'<line x1="{offset_x}" y1="{pos_y}" x2="{offset_x + board_size}" y2="{pos_y}" stroke="#0b381d" stroke-width="1.5"/>\n'

    # Four Star Points (standard Othello guide points at C/D-3, F/G-3, C/D-7, F/G-7 => grid lines 2 and 6)
    for sx in [2, 6]:
        for sy in [2, 6]:
            spx = offset_x + sx * cell_size
            spy = offset_y + sy * cell_size
            svg += f'<circle cx="{spx}" cy="{spy}" r="3.5" fill="#072412"/>\n'

    # Coordinate Labels
    for i in range(8):
        center_x = offset_x + i * cell_size + cell_size / 2
        center_y = offset_y + i * cell_size + cell_size / 2
        col_letter = cols_str[i]
        row_number = str(i + 1)

        # Top and bottom column letters
        svg += f'<text x="{center_x}" y="26" text-anchor="middle" dominant-baseline="middle" fill="#d1fae5" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="700">{col_letter}</text>\n'
        svg += f'<text x="{center_x}" y="496" text-anchor="middle" dominant-baseline="middle" fill="#d1fae5" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="700">{col_letter}</text>\n'

        # Left and right row numbers
        svg += f'<text x="24" y="{center_y}" text-anchor="middle" dominant-baseline="middle" fill="#d1fae5" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="700">{row_number}</text>\n'
        svg += f'<text x="496" y="{center_y}" text-anchor="middle" dominant-baseline="middle" fill="#d1fae5" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="700">{row_number}</text>\n'

    # Discs
    latest_flips_set = set(getattr(board, "latest_flips", []))
    for y in range(8):
        for x in range(8):
            cell = board.cells[y][x]
            if cell == EMPTY:
                continue

            cx = offset_x + x * cell_size + cell_size / 2
            cy = offset_y + y * cell_size + cell_size / 2
            is_latest = (x == board.latest_x and y == board.latest_y)
            is_flipped = (x, y) in latest_flips_set

            grad_id = "blackDisc" if cell == BLACK else "whiteDisc"
            stroke_col = "#18181b" if cell == BLACK else "#cbd5e1"
            anim_class = "latest-disc" if is_latest else ("flipped-disc" if is_flipped else "")

            # Disc element with 3D gradient and shadow
            svg += f'''
            <g class="{anim_class}">
                <circle cx="{cx}" cy="{cy}" r="{disc_radius}" fill="url(#{grad_id})" stroke="{stroke_col}" stroke-width="1.2" filter="url(#pieceShadow)"/>
            '''

            # Specular highlight on top left of disc
            if cell == BLACK:
                svg += f'<ellipse cx="{cx - 6}" cy="{cy - 6}" rx="7" ry="4" transform="rotate(-30 {cx - 6} {cy - 6})" fill="#71717a" opacity="0.35"/>\n'
            else:
                svg += f'<ellipse cx="{cx - 6}" cy="{cy - 6}" rx="7" ry="4" transform="rotate(-30 {cx - 6} {cy - 6})" fill="#ffffff" opacity="0.75"/>\n'

            # Indicator for the latest placed disc
            if is_latest:
                svg += f'''
                <circle cx="{cx}" cy="{cy}" r="{disc_radius + 4}" fill="none" stroke="#fbbf24" stroke-width="2.5" filter="url(#goldGlow)" class="latest-ring"/>
                <circle cx="{cx}" cy="{cy}" r="4" fill="#fbbf24"/>
                '''

            svg += '</g>\n'

    svg += '''
    </svg>
    </div>
    <style>
        .latest-ring {
            animation: pulseGlow 1.8s ease-in-out infinite;
        }
        .latest-disc {
            animation: placeDisc 0.35s ease-out;
            transform-origin: center;
        }
        .flipped-disc {
            animation: flipDisc 0.5s ease-in-out;
            transform-origin: center;
        }
        @keyframes pulseGlow {
            0%, 100% { opacity: 0.9; stroke-width: 2.5; }
            50% { opacity: 0.35; stroke-width: 4; }
        }
        @keyframes placeDisc {
            0% { transform: scale(0.6); opacity: 0.5; }
            80% { transform: scale(1.08); }
            100% { transform: scale(1); opacity: 1; }
        }
        @keyframes flipDisc {
            0% { transform: scaleX(1); }
            50% { transform: scaleX(0.1); opacity: 0.7; }
            100% { transform: scaleX(1); opacity: 1; }
        }
    </style>
    '''
    return svg