# generate a banner for the LAS Ecliptic
import gzip
import svgwrite

from math import atan2, cos, pi, sin, sqrt


bkgr_attrs = {  # SVG attributes of background rectangle
    'fill': '#060c64',  # from LAS logo
    'stroke': 'none',
}

eclpt_attrs = {  # SVG attributes of ecliptic line
    'stroke': '#ffc000',  # '#0100d7' is the other blue color from the logo, but it's too dark
    'stroke-width': '0.75',
    'stroke-linecap': 'round',
}

line_attrs = {  # SVG attributes of figure lines
    'stroke': '#f0e12c',  # from LAS logo
    'stroke-width': '0.75',
    'stroke-miterlimit': '4',
    'stroke-linecap': 'round',
}

star_attrs = {  # SVG attributes of stars
    'stroke': 'none',
    'fill': '#ffffff',
}

dwg_dpi = 100  # coordinates per inch (not really dots) in output SVG
dwg_bleed_width = 8.5 * dwg_dpi  # width of paper, converted to dwg units
dwg_border = 0.5 * dwg_dpi  # border in dwg units
dwg_sky_width = dwg_bleed_width - 2 * dwg_border
dwg_scale = dwg_sky_width / (2 * pi)  # scale for ecl lng --> dwg


def ecl_to_dwg(lng, lat, max_lng):  # convert ecliptic to drawing coordinates
    # ecliptic longitude decreases left to right on the chart
    # max_lng is on the left edge of the drawing, coordinate 0
    return dwg_scale * (max_lng - lng), dwg_scale * (pi / 2 - lat)


class Star:
    def __init__(self, hip_id=None, ra=None, dec=None, vmag=None):
        self.hip_id = hip_id
        self.ra = ra
        self.dec = dec
        self.vmag = vmag

        equx = cos(self.dec) * cos(self.ra)  # equatorial x, y, z coordinates
        equy = cos(self.dec) * sin(self.ra)
        equz = sin(self.dec)
        obl = 23.4376 * pi / 180  # true obliquity of the ecliptic for 1/1/2022
        eclx = equx  # ecliptic x, y, z coordinates
        ecly = equy * cos(obl) + equz * sin(obl)
        eclz = equz * cos(obl) - equy * sin(obl)
        self.ecl_lng = atan2(ecly, eclx)  # ecliptic longitude, radians
        self.ecl_lat = atan2(eclz, sqrt(eclx ** 2 + ecly ** 2))
        self.radius = dwg_scale * (7 - min(6.5, 0.8 * self.vmag)) / 400  # size of dot on chart


def load_hip_catalog():
    catalog = dict()  # HIP id --> Star
    discarded = 0
    vmag_limit = 7.0  # for speed
    with gzip.open('hip2.dat.gz', mode='r') as hip_file:  # see README.md for source of data file
        for line in hip_file:
            try:
                hip_id = int(line[0:6].strip())  # see README.md for source of record layout
                ra = float(line[15:28].strip())  # radians
                dec = float(line[29:42].strip())
                vmag = float(line[129:136].strip())
            except ValueError:
                print(f'Discarding: {line[:48]} ...')
                discarded += 1
                continue
            if vmag > vmag_limit:
                continue
            catalog[hip_id] = Star(hip_id=hip_id, vmag=vmag, ra=ra, dec=dec)
    print('HIP catalog:')
    print(f'{discarded} record(s) discarded')
    print(f'{len(catalog)} records loaded')
    print()
    return catalog


def get_figures():
    figures = dict()  # name --> list of hip_id pairs, one for each line segment
    stars_present = set()  # hip_ids present in figure lines
    with open('constellationship.fab') as fig_file:  # see README.md for source of data file
        for line in fig_file:
            line = line.strip()
            if line == '' or line[0] == '#':
                continue
            fields = line.split()
            name = fields.pop(0)
            count = int(fields.pop(0))
            fig = list()
            for i in range(count):
                id1 = int(fields.pop(0))
                id2 = int(fields.pop(0))
                fig.append((id1, id2))
                stars_present.add(id1)
                stars_present.add(id2)
            if len(fields) > 0:
                print('extra data found in a line of figures file:')
                print(line)
                break
            figures[name] = fig
    print('figure file:')
    print(f'{len(figures)} figures loaded')
    print(f'{len(stars_present)} stars used in figure lines')
    print()
    return figures, stars_present


def morse_coords(string, minc, maxc):  # convert a string to a list of line segment coords
    alphabet = {'a': '.-', 'b': '-...', 'c': '-.-.', 'd': '-..', 'e': '.', 'f': '..-.',
                'g': '--.', 'h': '....', 'i': '..', 'j': '.---', 'k': '-.-', 'l': '.-..',
                'm': '--', 'n': '-.', 'o': '---', 'p': '.--.', 'q': '--.-', 'r': '.-.',
                's': '...', 't': '-', 'u': '..-', 'v': '...-', 'w': '.--', 'x': '-..-',
                'y': '-.--', 'z': '--..', '1': '.----', '2': '..---', '3': '...--',
                '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
                '9': '----.', '0': '-----', ', ': '--..--', '.': '.-.-.-', '?': '..--..',
                '/': '-..-.', '-': '-....-', '(': '-.--.', ')': '-.--.-'
                }
    coords = list()
    x = 0.0
    for ch in string.strip():
        if ch == ' ':
            x += 6
        else:
            code = alphabet[ch]
            for symbol in code:
                if symbol == '-':
                    coords.append((x, x + 3))
                    x += 5  # lengths and spaces are not standard Morse, but look good
                else:
                    coords.append((x, x + 1))
                    x += 3
            x += 3
    scale = (maxc - minc) / (x - 2)
    return list([(x1 * scale + minc, x2 * scale + minc) for x1, x2 in coords])


def make_svg_layer(dwg, name):  # create SVG group
    group = dwg.g(id=name.lower())
    # the following will make it look like an Inkscape layer
    # but it needs more boilerplate at the document level to load cleanly
    # group.update({
    #     'inkscape:groupmode': 'layer',
    #     'inkscape:label': name,
    #     'style': 'display:inline',
    # })
    dwg.add(group)
    return group


def main():
    hip_catalog = load_hip_catalog()
    figures, stars_present = get_figures()

    zodiac = ['Ari', 'Tau', 'Gem', 'Cnc', 'Leo', 'Vir', 'Lib', 'Sco', 'Sgr', 'Aqr', 'Psc', 'Cap']
    fig_max_lng = dict()

    # look up ecliptic coordinates for figure lines
    fig_coords = dict()
    for name in zodiac:
        id_pairs = figures[name]
        coord_pairs = list()
        min_lng = float("inf")
        max_lng = -float("inf")
        for pair in id_pairs:
            coord_pair = list()
            for hip_id in pair:
                star = hip_catalog[hip_id]
                lng = star.ecl_lng
                lat = star.ecl_lat
                coord_pair.append([lng, lat])
                min_lng = min(min_lng, lng)
                max_lng = max(max_lng, lng)
            coord_pairs.append(coord_pair)
        if max_lng - min_lng > pi / 4:  # figure is cut by pi/-pi boundary
            center = (min_lng + max_lng) / 2
            max_lng = -float("inf")  # recalculate max
            for coord_pair in coord_pairs:
                for i in (0, 1):
                    if coord_pair[i][0] < center:
                        coord_pair[i][0] += 2 * pi  # fixed!
                    max_lng = max(max_lng, coord_pair[i][0])
        fig_coords[name] = coord_pairs
        fig_max_lng[name] = max_lng

    for anchor_name in sorted(zodiac):  # make a chart with each zodiac figure as the leftmost one
        filename = f'ecliptic_chart_beginning_with_{anchor_name.lower()}.svg'
        max_lng = fig_max_lng[anchor_name] + dwg_border / dwg_scale

        dwg = svgwrite.Drawing(filename, profile='tiny', size=(dwg_bleed_width, pi * dwg_scale), debug=False)

        group = make_svg_layer(dwg, 'Background')
        group.add(dwg.rect(insert=(0, 0), size=(dwg_bleed_width, pi * dwg_scale), **bkgr_attrs))

        group = make_svg_layer(dwg, 'Figures')
        for name in zodiac:
            figure = fig_coords[name]
            offset = -2 * pi if fig_max_lng[name] > fig_max_lng[anchor_name] else 0.0
            for line in figure:
                pair1, pair2 = line
                ex1, ey1 = pair1
                ex1 += offset
                ex2, ey2 = pair2
                ex2 += offset
                dx1, dy1 = ecl_to_dwg(ex1, ey1, max_lng)
                dx2, dy2 = ecl_to_dwg(ex2, ey2, max_lng)
                group.add(dwg.line((dx1, dy1), (dx2, dy2), **line_attrs))

        group = make_svg_layer(dwg, 'Stars')
        for hip_id in sorted(hip_catalog.keys()):  # sorting for repeatability
            star = hip_catalog[hip_id]
            for offset in (-2 * pi, 0, 2 * pi):  # draw star possibly multiple times to fill in borders
                ex1 = star.ecl_lng + offset
                ey1 = star.ecl_lat
                dx1, dy1 = ecl_to_dwg(ex1, ey1, max_lng)
                if 0.0 < dx1 < dwg_bleed_width:
                    if star.vmag < 3.5 or star.hip_id in stars_present:
                        group.add(dwg.circle((dx1, dy1), star.radius, **star_attrs))

        group = make_svg_layer(dwg, 'Ecliptic')
        x, y = ecl_to_dwg(0.0, 0.0, max_lng)
        coords = morse_coords('the ecliptic -- lackawanna astronomical society', dwg_border,
                              dwg_bleed_width - dwg_border)
        for x1, x2 in coords:
            group.add(dwg.line((x1, y), (x2, y), **eclpt_attrs))

        dwg.save()
        print(f'Created {filename}')


if __name__ == '__main__':
    main()
