import pygame
import asyncio
import sys
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Aplikasi Menggambar")

WHITE = (255, 255, 255)
GRAY = (230, 230, 230)
BLACK = (0, 0, 0)
screen.fill(WHITE)

colors = {
    'Hitam': BLACK,
    'Merah': (255, 0, 0),
    'Hijau': (0, 255, 0),
    'Biru': (0, 0, 255),
    'Kuning': (255, 255, 0),
    'Ungu': (128, 0, 128)
}

thickness_options = [1, 2, 3, 4, 5, 6, 8, 10]
modes = ['dot', 'freedraw', 'line', 'rect', 'circle', 'ellipse']

color = BLACK
mode = 'dot'
thickness = 2
drawing = False
start_pos = None
last_pos = None

font = pygame.font.SysFont(None, 24)
temp_surface = screen.copy()

# Tambah mode select
select_mode = False
selected_obj_idx = None
objects = []  # List untuk menyimpan objek gambar
windowing_rect = None
windowing_preview = False
selected_window_objs = []
windowing_drag = False
windowing_start = None
windowing_end = None
clipped_objects = []
clipping_active = False
clipping_rect = None
clip_index = None

# Daftar warna untuk kotak warna 2 baris
color_choices = [
    (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (128, 0, 128), (255, 128, 0), (0, 255, 255)
]
color_names = ['Hitam', 'Merah', 'Hijau', 'Biru', 'Kuning', 'Ungu', 'Oranye', 'Cyan']

def draw_grid():
    for x in range(100, WIDTH, 20):
        pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 20):
        pygame.draw.line(screen, GRAY, (100, y), (WIDTH, y))

def draw_menu():
    pygame.draw.rect(screen, (200, 200, 200), (0, 0, 100, HEIGHT))
    y = 10
    # Tombol select di atas objek
    select_box_h = 32
    pygame.draw.rect(screen, (0, 128, 255) if select_mode else GRAY, (10, y, 80, select_box_h), 2)
    label = font.render('select', True, BLACK)
    lx = 10 + (80 - label.get_width()) // 2
    ly = y + (select_box_h - label.get_height()) // 2
    screen.blit(label, (lx, ly))
    y += select_box_h + 10

    # Modes 2 kolom, kotak, label di tengah, singkat jika kepanjangan
    mode_box_w, mode_box_h = 40, 32
    modes_per_row = 2
    for i, m in enumerate(modes):
        row = i // modes_per_row
        col = i % modes_per_row
        x_box = 10 + col * (mode_box_w + 10)
        y_box = y + row * (mode_box_h + 8)
        pygame.draw.rect(screen, BLACK if mode == m and not select_mode else GRAY, (x_box, y_box, mode_box_w, mode_box_h), 2)
        label_text = m
        label = font.render(label_text, True, BLACK)
        while label.get_width() > mode_box_w - 6 and len(label_text) > 2:
            label_text = label_text[:-1]
            label = font.render(label_text + '.', True, BLACK)
        if label.get_width() > mode_box_w - 6:
            label = font.render(label_text[0] + '.', True, BLACK)
        lx = x_box + (mode_box_w - label.get_width()) // 2
        ly = y_box + (mode_box_h - label.get_height()) // 2
        screen.blit(label, (lx, ly))
    y += ((len(modes) + 1) // modes_per_row) * (mode_box_h + 8) + 10

    # Kotak warna 2 kolom ke bawah (vertikal)
    color_box_size = 28
    color_box_gap = 6
    for i, c in enumerate(color_choices):
        col = i % 2
        row = i // 2
        bx = 10 + col * (color_box_size + color_box_gap)
        by = y + row * (color_box_size + color_box_gap)
        pygame.draw.rect(screen, c, (bx, by, color_box_size, color_box_size))
        pygame.draw.rect(screen, BLACK, (bx, by, color_box_size, color_box_size), 2)
        if c == color:
            pygame.draw.rect(screen, (0, 128, 255), (bx-2, by-2, color_box_size+4, color_box_size+4), 2)
    y += 4 * (color_box_size + color_box_gap) + 5

    # Tombol clear
    pygame.draw.rect(screen, WHITE, (10, y, 80, 30))
    pygame.draw.rect(screen, BLACK, (10, y, 80, 30), 1)
    screen.blit(font.render("Clear", True, BLACK), (20, y + 5))
    y += 40
    # Tombol delete
    pygame.draw.rect(screen, WHITE, (10, y, 80, 30))
    pygame.draw.rect(screen, BLACK, (10, y, 80, 30), 1)
    screen.blit(font.render("Delete", True, BLACK), (18, y + 5))
    y += 40

    screen.blit(font.render("Ketebalan:", True, BLACK), (10, y))
    y += 25

    for i in range(0, len(thickness_options), 2):
        t1 = thickness_options[i]
        pygame.draw.rect(screen, BLACK if thickness == t1 else GRAY, (10, y, 30, 20))
        screen.blit(font.render(str(t1), True, WHITE), (15, y))
        if i + 1 < len(thickness_options):
            t2 = thickness_options[i + 1]
            pygame.draw.rect(screen, BLACK if thickness == t2 else GRAY, (50, y, 30, 20))
            screen.blit(font.render(str(t2), True, WHITE), (55, y))
        y += 30

    # Highlight mode windowing jika aktif
    if mode == 'windowing':
        windowing_label = font.render('Windowing', True, BLACK)
        screen.blit(windowing_label, (10, 10))

def handle_menu_click(pos):
    global mode, color, thickness, select_mode, selected_obj_idx, objects, selected_window_objs, clipping_active, clipping_rect, clip_index
    x, y = pos
    if x > 100:
        return
    y_offset = 10
    # Tombol select
    if 10 <= x <= 90 and y_offset <= y <= y_offset + 32:
        select_mode = True
        mode = None
        selected_obj_idx = None
        return
    y_offset += 32 + 10
    # Modes 2 kolom
    mode_box_w, mode_box_h = 40, 32
    modes_per_row = 2
    mode_rows = ((len(modes) + 1) // modes_per_row)
    mode_area_h = mode_rows * (mode_box_h + 8)
    for i, m in enumerate(modes):
        row = i // modes_per_row
        col = i % modes_per_row
        x_box = 10 + col * (mode_box_w + 10)
        y_box = y_offset + row * (mode_box_h + 8)
        if x_box <= x <= x_box + mode_box_w and y_box <= y <= y_box + mode_box_h:
            mode = m
            select_mode = False
            selected_obj_idx = None
            return
    y_offset += mode_area_h + 10
    # Kotak warna 2 kolom ke bawah (vertikal)
    color_box_size = 28
    color_box_gap = 6
    for i, c in enumerate(color_choices):
        col = i % 2
        row = i // 2
        bx = 10 + col * (color_box_size + color_box_gap)
        by = y_offset + row * (color_box_size + color_box_gap)
        if bx <= x <= bx + color_box_size and by <= y <= by + color_box_size:
            color = c
            return
    y_offset += 4 * (color_box_size + color_box_gap) + 5
    # Tombol clear
    if 10 <= x <= 90 and y_offset <= y <= y_offset + 30:
        screen.fill(WHITE)
        draw_grid()
        objects.clear()
        selected_obj_idx = None
        selected_window_objs.clear()
        clipping_active = False
        clipping_rect = None
        clip_index = None
        return
    y_offset += 40
    # Tombol delete
    if 10 <= x <= 90 and y_offset <= y <= y_offset + 30:
        if selected_obj_idx is not None and 0 <= selected_obj_idx < len(objects):
            del objects[selected_obj_idx]
            selected_obj_idx = None
        return
    y_offset += 40
    # Label ketebalan
    y_offset += 25
    for i in range(0, len(thickness_options), 2):
        y_box = y_offset + (i // 2) * 30
        if 10 <= x <= 40 and y_box <= y <= y_box + 20:
            thickness = thickness_options[i]
            for idx in selected_window_objs:
                obj = objects[idx]
                obj['thickness'] = thickness
            return
        if i + 1 < len(thickness_options):
            if 50 <= x <= 80 and y_box <= y <= y_box + 20:
                thickness = thickness_options[i + 1]
                for idx in selected_window_objs:
                    obj = objects[idx]
                    obj['thickness'] = thickness
                return

    # Highlight mode windowing jika aktif
    if mode == 'windowing':
        windowing_label = font.render('Windowing', True, BLACK)
        screen.blit(windowing_label, (10, 10))

def draw_all_objects():
    if clipping_active and clipping_rect and clip_index is not None:
        temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Gambar objek lama (sebelum windowing) ke surface sementara
        for i, obj in enumerate(objects):
            if i >= clip_index:
                continue
            if obj['type'] == 'freedraw':
                pts = obj['points']
                for k in range(1, len(pts)):
                    pygame.draw.line(temp, obj['color'], pts[k-1], pts[k], obj['thickness'])
            elif obj['type'] == 'dot':
                pygame.draw.circle(temp, obj['color'], obj['start'], obj['thickness'])
            else:
                draw_shape(temp, obj['type'], obj['start'], obj['end'], obj['color'], obj['thickness'], obj.get('angle',0), obj.get('scale',1))
        # Blit hanya bagian dalam clipping_rect
        clip_surf = temp.subsurface(clipping_rect).copy()
        screen.blit(clip_surf, (clipping_rect.left, clipping_rect.top))
        # Hilangkan garis kotak biru di canvas (hapus pygame.draw.rect(screen, (0,0,255), ...))
        # Gambar objek baru (setelah windowing) tanpa clipping
        for i, obj in enumerate(objects):
            if i < clip_index:
                continue
            if obj['type'] == 'freedraw':
                pts = obj['points']
                for k in range(1, len(pts)):
                    pygame.draw.line(screen, obj['color'], pts[k-1], pts[k], obj['thickness'])
            elif obj['type'] == 'dot':
                pygame.draw.circle(screen, obj['color'], obj['start'], obj['thickness'])
            else:
                draw_shape(screen, obj['type'], obj['start'], obj['end'], obj['color'], obj['thickness'], obj.get('angle',0), obj.get('scale',1))
        # Highlight dan handle select untuk semua objek
        for idx, obj in enumerate(objects):
            if idx == selected_obj_idx:
                pygame.draw.rect(screen, (0,255,0), obj['bbox'], 2)
                # Gambar handle di setiap sudut bbox
                bbox = obj['bbox']
                handle_size = 8
                handles = [
                    (bbox.left, bbox.top),
                    (bbox.right, bbox.top),
                    (bbox.right, bbox.bottom),
                    (bbox.left, bbox.bottom)
                ]
                for hx, hy in handles:
                    pygame.draw.rect(screen, (255,0,0), (hx-handle_size//2, hy-handle_size//2, handle_size, handle_size))
                # Gambar handle rotasi di sisi tengah
                side_size = 10
                sides = [
                    ((bbox.left + bbox.right)//2, bbox.top),
                    (bbox.right, (bbox.top + bbox.bottom)//2),
                    ((bbox.left + bbox.right)//2, bbox.bottom),
                    (bbox.left, (bbox.top + bbox.bottom)//2)
                ]
                for sx, sy in sides:
                    pygame.draw.rect(screen, (0,0,255), (sx-side_size//2, sy-side_size//2, side_size, side_size))
    else:
        for idx, obj in enumerate(objects):
            if idx == selected_obj_idx:
                pygame.draw.rect(screen, (0,255,0), obj['bbox'], 2)
                # Gambar handle di setiap sudut bbox
                bbox = obj['bbox']
                handle_size = 8
                handles = [
                    (bbox.left, bbox.top),
                    (bbox.right, bbox.top),
                    (bbox.right, bbox.bottom),
                    (bbox.left, bbox.bottom)
                ]
                for hx, hy in handles:
                    pygame.draw.rect(screen, (255,0,0), (hx-handle_size//2, hy-handle_size//2, handle_size, handle_size))
                # Gambar handle rotasi di sisi tengah
                side_size = 10
                sides = [
                    ((bbox.left + bbox.right)//2, bbox.top),
                    (bbox.right, (bbox.top + bbox.bottom)//2),
                    ((bbox.left + bbox.right)//2, bbox.bottom),
                    (bbox.left, (bbox.top + bbox.bottom)//2)
                ]
                for sx, sy in sides:
                    pygame.draw.rect(screen, (0,0,255), (sx-side_size//2, sy-side_size//2, side_size, side_size))
            if obj['type'] == 'freedraw':
                pts = obj['points']
                for i in range(1, len(pts)):
                    pygame.draw.line(screen, obj['color'], pts[i-1], pts[i], obj['thickness'])
            elif obj['type'] == 'dot':
                pygame.draw.circle(screen, obj['color'], obj['start'], obj['thickness'])
            else:
                draw_shape(screen, obj['type'], obj['start'], obj['end'], obj['color'], obj['thickness'], obj.get('angle',0), obj.get('scale',1))
    # Gambar hasil clipping jika ada
    for obj in clipped_objects:
        if obj['type'] == 'line':
            pygame.draw.line(screen, obj['color'], obj['start'], obj['end'], obj['thickness'])
        elif obj['type'] == 'dot':
            pygame.draw.circle(screen, obj['color'], obj['start'], obj['thickness'])
        elif obj['type'] == 'freedraw':
            pts = obj['points']
            for i in range(1, len(pts)):
                pygame.draw.line(screen, obj['color'], pts[i-1], pts[i], obj['thickness'])
        else:
            draw_shape(screen, obj['type'], obj['start'], obj['end'], obj['color'], obj['thickness'])

# Ubah draw_shape agar bisa handle angle dan scale (sementara hanya translasi dulu)
def draw_shape(surface, shape_mode, start, end, color, thick, angle=0, scale=1):
    if angle and shape_mode in ['rect', 'ellipse', 'line']:
        # Rotasi rect, ellipse, line
        cx = (start[0] + end[0]) / 2
        cy = (start[1] + end[1]) / 2
        if shape_mode == 'rect':
            w = abs(end[0] - start[0])
            h = abs(end[1] - start[1])
            points = [(-w/2,-h/2), (w/2,-h/2), (w/2,h/2), (-w/2,h/2)]
            rot_points = []
            for px, py in points:
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                rot_points.append((int(cx+rx), int(cy+ry)))
            pygame.draw.polygon(surface, color, rot_points, thick)
        elif shape_mode == 'ellipse':
            # Rotasi ellipse: gambar ke surface sementara lalu rotate
            w = abs(end[0] - start[0])
            h = abs(end[1] - start[1])
            temp = pygame.Surface((w+thick*2, h+thick*2), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (thick, thick, w, h), thick)
            rot_img = pygame.transform.rotate(temp, -math.degrees(angle))
            rect = rot_img.get_rect(center=(int(cx), int(cy)))
            surface.blit(rot_img, rect.topleft)
        elif shape_mode == 'line':
            x1, y1 = start
            x2, y2 = end
            # Rotasi kedua titik
            for pt in [(x1, y1), (x2, y2)]:
                px, py = pt[0] - cx, pt[1] - cy
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                if pt == (x1, y1):
                    nx1, ny1 = int(cx+rx), int(cy+ry)
                else:
                    nx2, ny2 = int(cx+rx), int(cy+ry)
            pygame.draw.line(surface, color, (nx1, ny1), (nx2, ny2), thick)
    else:
        # Untuk transformasi lebih lanjut, implementasi scale/rotasi bisa ditambah
        if shape_mode == 'line':
            pygame.draw.line(surface, color, start, end, thick)
        elif shape_mode == 'rect':
            rect = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                               abs(end[0] - start[0]), abs(end[1] - start[1]))
            pygame.draw.rect(surface, color, rect, thick)
        elif shape_mode == 'circle':
            radius = int(((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5)
            pygame.draw.circle(surface, color, start, radius, thick)
        elif shape_mode == 'ellipse':
            rect = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                               abs(end[0] - start[0]), abs(end[1] - start[1]))
            pygame.draw.ellipse(surface, color, rect, thick)

async def main():
    global drawing, start_pos, last_pos, temp_surface, select_mode, selected_obj_idx, windowing_rect, windowing_preview, selected_window_objs, windowing_drag, windowing_start, windowing_end, clipped_objects, clipping_active, clipping_rect, clip_index
    clock = pygame.time.Clock()
    draw_grid()

    dragging_obj = False
    drag_offset = (0,0)
    preview_shape = None
    preview_args = None
    freedraw_points = []
    scaling = False
    scaling_handle = None
    scaling_start = None
    scaling_bbox0 = None
    scaling_obj_idx = None
    rotating = False
    rotating_side = None
    rotating_start_angle = None
    rotating_obj_idx = None
    rotating_center = None
    scaling_freedraw_points0 = None
    rotating_freedraw_points0 = None
    rotating_freedraw_center0 = None
    drag_start_mouse = None
    drag_start_bbox = None
    drag_start_start = None
    drag_start_end = None
    drag_start_points = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Klik kanan untuk windowing
                    windowing_drag = True
                    windowing_start = event.pos
                    windowing_end = event.pos
                    windowing_preview = True
                    windowing_rect = None
                elif event.button == 1:
                    if event.pos[0] <= 100:
                        handle_menu_click(event.pos)
                    else:
                        if mode == 'windowing':
                            drawing = True
                            start_pos = event.pos
                            last_pos = event.pos
                            windowing_preview = True
                            windowing_rect = None
                        if select_mode and selected_obj_idx is not None:
                            obj = objects[selected_obj_idx]
                            bbox = obj['bbox']
                            handle_size = 8
                            side_size = 10
                            handles = [
                                (bbox.left, bbox.top),
                                (bbox.right, bbox.top),
                                (bbox.right, bbox.bottom),
                                (bbox.left, bbox.bottom)
                            ]
                            sides = [
                                ((bbox.left + bbox.right)//2, bbox.top),
                                (bbox.right, (bbox.top + bbox.bottom)//2),
                                ((bbox.left + bbox.right)//2, bbox.bottom),
                                (bbox.left, (bbox.top + bbox.bottom)//2)
                            ]
                            for idx, (hx, hy) in enumerate(handles):
                                handle_rect = pygame.Rect(hx-handle_size//2, hy-handle_size//2, handle_size, handle_size)
                                if handle_rect.collidepoint(event.pos):
                                    scaling = True
                                    scaling_handle = idx
                                    scaling_start = event.pos
                                    scaling_bbox0 = bbox.copy()
                                    scaling_obj_idx = selected_obj_idx
                                    if obj['type'] == 'freedraw':
                                        scaling_freedraw_points0 = list(obj['points'])
                                    break
                            else:
                                for idx, (sx, sy) in enumerate(sides):
                                    side_rect = pygame.Rect(sx-side_size//2, sy-side_size//2, side_size, side_size)
                                    if side_rect.collidepoint(event.pos):
                                        rotating = True
                                        rotating_side = idx
                                        rotating_obj_idx = selected_obj_idx
                                        cx, cy = bbox.center
                                        rotating_center = (cx, cy)
                                        mx, my = event.pos
                                        dx = mx - cx
                                        dy = my - cy
                                        rotating_start_angle = (math.atan2(dy, dx) - objects[selected_obj_idx].get('angle',0))
                                        if obj['type'] == 'freedraw':
                                            rotating_freedraw_points0 = list(obj['points'])
                                            xs = [p[0] for p in obj['points']]
                                            ys = [p[1] for p in obj['points']]
                                            min_x, max_x = min(xs), max(xs)
                                            min_y, max_y = min(ys), max(ys)
                                            rotating_freedraw_center0 = ((min_x + max_x) / 2, (min_y + max_y) / 2)
                                        break
                                else:
                                    # Translasi (dalam kotak)
                                    for idx2, obj2 in enumerate(reversed(objects)):
                                        bbox2 = obj2['bbox']
                                        if bbox2.collidepoint(event.pos):
                                            selected_obj_idx = len(objects) - 1 - idx2
                                            dragging_obj = True
                                            drag_offset = (event.pos[0] - bbox2.x, event.pos[1] - bbox2.y)
                                            drag_start_mouse = event.pos
                                            drag_start_bbox = bbox2.copy()
                                            if obj2['type'] in ['rect', 'ellipse', 'line', 'circle']:
                                                drag_start_start = obj2['start']
                                                drag_start_end = obj2['end']
                                            elif obj2['type'] == 'freedraw':
                                                drag_start_points = list(obj2['points'])
                                            break
                        elif select_mode:
                            for idx, obj in enumerate(reversed(objects)):
                                bbox = obj['bbox']
                                if bbox.collidepoint(event.pos):
                                    selected_obj_idx = len(objects) - 1 - idx
                                    dragging_obj = True
                                    drag_offset = (event.pos[0] - bbox.x, event.pos[1] - bbox.y)
                                    break
                        else:
                            drawing = True
                            start_pos = event.pos
                            last_pos = event.pos
                            temp_surface = screen.copy()
                            preview_shape = None
                            preview_args = None
                            if mode == 'dot':
                                bbox = pygame.Rect(event.pos[0]-thickness, event.pos[1]-thickness, thickness*2, thickness*2)
                                objects.append({'type': 'dot', 'start': event.pos, 'end': event.pos, 'color': color, 'thickness': thickness, 'bbox': bbox, 'angle': 0, 'scale': 1})
                                pygame.draw.circle(screen, color, event.pos, thickness)
                                drawing = False
                                start_pos = None
                            elif mode == 'freedraw':
                                freedraw_points = [event.pos]
                                pygame.draw.circle(screen, color, event.pos, thickness)

            elif event.type == pygame.MOUSEMOTION:
                if windowing_drag:
                    windowing_end = event.pos
                    windowing_rect = pygame.Rect(min(windowing_start[0], windowing_end[0]), min(windowing_start[1], windowing_end[1]), abs(windowing_end[0] - windowing_start[0]), abs(windowing_end[1] - windowing_start[1]))
                if drawing and mode == 'windowing':
                    last_pos = event.pos
                    windowing_rect = pygame.Rect(min(start_pos[0], last_pos[0]), min(start_pos[1], last_pos[1]), abs(last_pos[0] - start_pos[0]), abs(last_pos[1] - start_pos[1]))
                if drawing:
                    if mode == 'freedraw':
                        pygame.draw.line(screen, color, last_pos, event.pos, thickness)
                        freedraw_points.append(event.pos)
                        last_pos = event.pos
                    elif mode in ['line', 'rect', 'circle', 'ellipse']:
                        screen.blit(temp_surface, (0, 0))
                        draw_shape(screen, mode, start_pos, event.pos, color, thickness)
                        preview_shape = mode
                        preview_args = (start_pos, event.pos, color, thickness)
                elif select_mode and scaling and scaling_obj_idx is not None:
                    obj = objects[scaling_obj_idx]
                    bbox0 = scaling_bbox0
                    mx0, my0 = scaling_start
                    mx, my = event.pos
                    handles = [
                        (bbox0.left, bbox0.top),
                        (bbox0.right, bbox0.top),
                        (bbox0.right, bbox0.bottom),
                        (bbox0.left, bbox0.bottom)
                    ]
                    opp_handle = (scaling_handle + 2) % 4
                    ox, oy = handles[opp_handle]
                    if obj['type'] == 'circle':
                        # Scaling circle: pusat tetap, radius berubah
                        cx = bbox0.centerx
                        cy = bbox0.centery
                        # Hitung radius baru dari pusat ke mouse
                        radius = int(max(abs(mx - cx), abs(my - cy)))
                        if radius < 3: radius = 3
                        obj['bbox'].x = cx - radius
                        obj['bbox'].y = cy - radius
                        obj['bbox'].width = obj['bbox'].height = radius * 2
                        obj['start'] = (cx, cy)
                        obj['end'] = (cx + radius, cy)
                    elif obj['type'] == 'freedraw':
                        # Scaling freedraw: gunakan bbox dan points awal
                        if scaling_freedraw_points0 is not None:
                            old_cx = bbox0.centerx
                            old_cy = bbox0.centery
                            old_w = bbox0.width if bbox0.width != 0 else 1
                            old_h = bbox0.height if bbox0.height != 0 else 1
                            new_w = abs(mx - ox)
                            new_h = abs(my - oy)
                            if new_w < 5: new_w = 5
                            if new_h < 5: new_h = 5
                            cx = (mx + ox) / 2
                            cy = (my + oy) / 2
                            scale_x = new_w / old_w
                            scale_y = new_h / old_h
                            new_points = []
                            for px, py in scaling_freedraw_points0:
                                relx = px - old_cx
                                rely = py - old_cy
                                npx = cx + relx * scale_x
                                npy = cy + rely * scale_y
                                new_points.append((int(npx), int(npy)))
                            obj['points'] = new_points
                            xs = [p[0] for p in obj['points']]
                            ys = [p[1] for p in obj['points']]
                            min_x, max_x = min(xs), max(xs)
                            min_y, max_y = min(ys), max(ys)
                            obj['bbox'].x = min_x
                            obj['bbox'].y = min_y
                            obj['bbox'].width = max_x - min_x
                            obj['bbox'].height = max_y - min_y
                    else:
                        new_w = abs(mx - ox)
                        new_h = abs(my - oy)
                        if new_w < 5: new_w = 5
                        if new_h < 5: new_h = 5
                        left = min(mx, ox)
                        right = max(mx, ox)
                        top = min(my, oy)
                        bottom = max(my, oy)
                        obj['bbox'].x = left
                        obj['bbox'].y = top
                        obj['bbox'].width = right - left
                        obj['bbox'].height = bottom - top
                        if obj['type'] in ['rect', 'ellipse', 'line']:
                            if scaling_handle == 0:
                                obj['start'] = (left, top)
                                obj['end'] = (right, bottom)
                            elif scaling_handle == 1:
                                obj['start'] = (right, top)
                                obj['end'] = (left, bottom)
                            elif scaling_handle == 2:
                                obj['start'] = (right, bottom)
                                obj['end'] = (left, top)
                            elif scaling_handle == 3:
                                obj['start'] = (left, bottom)
                                obj['end'] = (right, top)
                        elif obj['type'] == 'freedraw':
                            cx = (left + right) / 2
                            cy = (top + bottom) / 2
                            old_cx = bbox0.centerx
                            old_cy = bbox0.centery
                            scale_x = (right - left) / bbox0.width if bbox0.width != 0 else 1
                            scale_y = (bottom - top) / bbox0.height if bbox0.height != 0 else 1
                            new_points = []
                            for px, py in obj['points']:
                                relx = px - old_cx
                                rely = py - old_cy
                                npx = cx + relx * scale_x
                                npy = cy + rely * scale_y
                                new_points.append((int(npx), int(npy)))
                            obj['points'] = new_points
                        elif obj['type'] == 'dot':
                            obj['start'] = (obj['bbox'].centerx, obj['bbox'].centery)
                            obj['end'] = obj['start']

                elif select_mode and rotating and rotating_obj_idx is not None:
                    # Rotasi objek
                    obj = objects[rotating_obj_idx]
                    cx, cy = rotating_center
                    mx, my = event.pos
                    dx = mx - cx
                    dy = my - cy
                    angle = math.atan2(dy, dx) - rotating_start_angle
                    if obj['type'] == 'freedraw':
                        # Rotasi semua titik terhadap pusat awal dan points awal
                        if rotating_freedraw_points0 is not None and rotating_freedraw_center0 is not None:
                            new_points = []
                            for px, py in rotating_freedraw_points0:
                                relx = px - rotating_freedraw_center0[0]
                                rely = py - rotating_freedraw_center0[1]
                                r = math.hypot(relx, rely)
                                theta = math.atan2(rely, relx) + angle
                                npx = rotating_freedraw_center0[0] + r * math.cos(theta)
                                npy = rotating_freedraw_center0[1] + r * math.sin(theta)
                                new_points.append((int(npx), int(npy)))
                            obj['points'] = new_points
                            xs = [p[0] for p in obj['points']]
                            ys = [p[1] for p in obj['points']]
                            min_x, max_x = min(xs), max(xs)
                            min_y, max_y = min(ys), max(ys)
                            obj['bbox'].x = min_x
                            obj['bbox'].y = min_y
                            obj['bbox'].width = max_x - min_x
                            obj['bbox'].height = max_y - min_y
                            obj['angle'] = angle
                    else:
                        obj['angle'] = angle
                elif select_mode and dragging_obj and selected_obj_idx is not None:
                    obj = objects[selected_obj_idx]
                    if drag_start_mouse is not None and drag_start_bbox is not None:
                        dx = event.pos[0] - drag_start_mouse[0]
                        dy = event.pos[1] - drag_start_mouse[1]
                        if obj['type'] in ['rect', 'ellipse', 'line', 'circle']:
                            obj['bbox'].x = drag_start_bbox.x + dx
                            obj['bbox'].y = drag_start_bbox.y + dy
                            obj['start'] = (drag_start_start[0] + dx, drag_start_start[1] + dy)
                            obj['end'] = (drag_start_end[0] + dx, drag_start_end[1] + dy)
                        elif obj['type'] == 'freedraw':
                            obj['points'] = [(px + dx, py + dy) for (px, py) in drag_start_points]
                            xs = [p[0] for p in obj['points']]
                            ys = [p[1] for p in obj['points']]
                            min_x, max_x = min(xs), max(xs)
                            min_y, max_y = min(ys), max(ys)
                            obj['bbox'].x = min_x
                            obj['bbox'].y = min_y
                            obj['bbox'].width = max_x - min_x
                            obj['bbox'].height = max_y - min_y
                        elif obj['type'] == 'dot':
                            obj['bbox'].x = drag_start_bbox.x + dx
                            obj['bbox'].y = drag_start_bbox.y + dy
                            cx = obj['bbox'].centerx
                            cy = obj['bbox'].centery
                            obj['start'] = (cx, cy)
                            obj['end'] = obj['start']

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3 and windowing_drag:
                    windowing_drag = False
                    windowing_preview = False
                    if windowing_rect:
                        clipping_active = True
                        clipping_rect = windowing_rect.copy()
                        clip_index = len(objects)
                        # Ubah warna objek yang terkena windowing menjadi biru
                        for i, obj in enumerate(objects):
                            if i < clip_index and obj['bbox'].colliderect(clipping_rect):
                                obj['color'] = (0, 0, 255)
                    windowing_rect = None
                    windowing_start = None
                    windowing_end = None
                if event.button == 1:
                    if drawing and mode == 'windowing':
                        drawing = False
                        windowing_preview = False
                        if windowing_rect:
                            selected_window_objs = []
                            for idx, obj in enumerate(objects):
                                if windowing_rect.contains(obj['bbox']):
                                    selected_window_objs.append(idx)
                        start_pos = None
                        last_pos = None
                        windowing_rect = None
                    if drawing:
                        # Tandai objek baru sebagai clipped jika clipping aktif
                        if clipping_active and clipping_rect:
                            if len(objects) > 0:
                                objects[-1]['clipped'] = True
                        if mode in ['line', 'rect', 'ellipse']:
                            bbox = pygame.Rect(min(start_pos[0], event.pos[0]), min(start_pos[1], event.pos[1]), abs(event.pos[0] - start_pos[0]), abs(event.pos[1] - start_pos[1]))
                            objects.append({'type': mode, 'start': start_pos, 'end': event.pos, 'color': color, 'thickness': thickness, 'bbox': bbox, 'angle': 0, 'scale': 1})
                        if mode == 'circle':
                            cx, cy = start_pos
                            ex, ey = event.pos
                            radius = int(((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5)
                            bbox = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
                            objects.append({'type': 'circle', 'start': start_pos, 'end': event.pos, 'color': color, 'thickness': thickness, 'bbox': bbox, 'angle': 0, 'scale': 1})
                        if mode == 'freedraw' and len(freedraw_points) > 1:
                            min_x = min(p[0] for p in freedraw_points)
                            min_y = min(p[1] for p in freedraw_points)
                            max_x = max(p[0] for p in freedraw_points)
                            max_y = max(p[1] for p in freedraw_points)
                            bbox = pygame.Rect(min_x, min_y, max_x-min_x, max_y-min_y)
                            objects.append({'type': 'freedraw', 'points': list(freedraw_points), 'color': color, 'thickness': thickness, 'bbox': bbox, 'angle': 0, 'scale': 1})
                        drawing = False
                        start_pos = None
                        preview_shape = None
                        preview_args = None
                        freedraw_points = []
                    if select_mode:
                        dragging_obj = False
                        drag_offset = None
                        drag_start_mouse = None
                        drag_start_bbox = None
                        drag_start_start = None
                        drag_start_end = None
                        drag_start_points = None
                        scaling = False
                        scaling_handle = None
                        scaling_start = None
                        scaling_bbox0 = None
                        scaling_obj_idx = None
                        scaling_freedraw_points0 = None
                        rotating = False
                        rotating_side = None
                        rotating_start_angle = None
                        rotating_obj_idx = None
                        rotating_center = None
                        rotating_freedraw_points0 = None
                        rotating_freedraw_center0 = None

        screen.fill(WHITE)
        draw_grid()
        draw_all_objects()
        # Preview windowing rectangle (tipis/transparan)
        if windowing_preview and windowing_rect:
            s = pygame.Surface((windowing_rect.width, windowing_rect.height), pygame.SRCALPHA)
            s.fill((0,200,255,60))
            screen.blit(s, (windowing_rect.x, windowing_rect.y))
            pygame.draw.rect(screen, (0,200,255), windowing_rect, 2)
        # Tampilkan preview shape jika sedang drag line/rect/circle/ellipse
        if drawing and preview_shape and preview_args:
            draw_shape(screen, preview_shape, *preview_args)
        # Tampilkan preview freedraw secara real-time
        if drawing and mode == 'freedraw' and len(freedraw_points) > 1:
            for i in range(1, len(freedraw_points)):
                pygame.draw.line(screen, color, freedraw_points[i-1], freedraw_points[i], thickness)
        draw_menu()
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

# Untuk pygbag
asyncio.run(main())