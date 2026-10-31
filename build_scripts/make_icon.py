"""Draw the app icon: a folder with a document and a green check badge on a
blue rounded square - "fill in once, folders and documents are done".

Writes resources/app_icon.png (1024px, for previews) and
resources/app_icon.ico (16-256px, used by PyInstaller, Inno Setup and the
window title bar). Run from anywhere: python build_scripts/make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SIZE = 1024
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]

BLUE_TOP = (43, 108, 176)
BLUE_BOTTOM = (31, 78, 121)
FOLDER_BACK = (224, 169, 46)
FOLDER_FRONT = (246, 196, 83)
PAPER = (255, 255, 255)
PAPER_LINE = (157, 183, 213)
GREEN = (46, 158, 91)
WHITE = (255, 255, 255)


def draw(size: int = SIZE) -> Image.Image:
    s = size / SIZE  # all coordinates below are on a 1024 grid

    def box(x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float]:
        return (x0 * s, y0 * s, x1 * s, y1 * s)

    # Background: vertical gradient clipped to a rounded square.
    gradient = Image.new("RGB", (size, size))
    gd = ImageDraw.Draw(gradient)
    for y in range(size):
        t = y / max(size - 1, 1)
        gd.line([(0, y), (size, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(BLUE_TOP, BLUE_BOTTOM)))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box(40, 40, 984, 984), radius=200 * s, fill=255)
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    image.paste(gradient, (0, 0), mask)

    d = ImageDraw.Draw(image)
    # Folder back with its tab.
    d.rounded_rectangle(box(190, 300, 470, 420), radius=40 * s, fill=FOLDER_BACK)
    d.rounded_rectangle(box(190, 360, 834, 800), radius=56 * s, fill=FOLDER_BACK)
    # Document sticking out of the folder.
    d.rounded_rectangle(box(300, 220, 724, 640), radius=28 * s, fill=PAPER)
    for y in (310, 380, 450):
        d.rounded_rectangle(box(360, y, 664, y + 30), radius=15 * s, fill=PAPER_LINE)
    # Folder front.
    d.rounded_rectangle(box(170, 500, 854, 820), radius=56 * s, fill=FOLDER_FRONT)
    # Green check badge, bottom right, with a white ring.
    d.ellipse(box(600, 600, 940, 940), fill=WHITE)
    d.ellipse(box(626, 626, 914, 914), fill=GREEN)
    d.line(
        [(690 * s, 775 * s), (752 * s, 838 * s), (858 * s, 712 * s)],
        fill=WHITE,
        width=round(46 * s),
        joint="curve",
    )
    return image


def main() -> None:
    big = draw()
    big.save(ROOT / "resources" / "app_icon.png")
    # Draw the small sizes from a 4x supersample each, so thin parts stay crisp.
    frames = [draw(size * 4).resize((size, size), Image.LANCZOS) for size in ICO_SIZES]
    frames[-1].save(
        ROOT / "resources" / "app_icon.ico",
        sizes=[(size, size) for size in ICO_SIZES],
        append_images=frames[:-1],
    )
    print("Wrote resources/app_icon.png and resources/app_icon.ico")


if __name__ == "__main__":
    main()
