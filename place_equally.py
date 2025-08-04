import math
import pcbnew
import random
import wx

def debug(msg):
    wx.MessageBox(msg, 'debug')

class Footprint:
    def __init__(self, fp, is_ignored = False):
        self.is_ignored = is_ignored
        self.ref = fp.GetReference()
        self.layer = fp.GetLayer()

        # we want bounding box without labels
        ref_visible = fp.Reference().IsVisible()
        val_visible = fp.Value().IsVisible()
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.InvalidateGeometryCaches()

        self.pos = pcbnew.VECTOR2I(fp.GetPosition())
        fbbox = fp.GetBoundingBox()
        self.bbox = pcbnew.BOX2I(fbbox.GetPosition(), fbbox.GetSize())
        self.layer = fp.GetLayer()

        # bring back the defaults
        fp.Reference().SetVisible(ref_visible)
        fp.Value().SetVisible(val_visible)
        fp.InvalidateGeometryCaches()

        # store pads positions
        self.pads = {}
        for pad in fp.Pads():
            net = pad.GetNet()
            if net:
                net_name = net.GetNetname()
                if not net_name in self.pads:
                    self.pads[net_name] = []

                pad_pos = pcbnew.VECTOR2I(pad.GetPosition())
                self.pads[net_name].append(pad_pos)

    def shift(self, offset):
        self.bbox = pcbnew.BOX2I(self.bbox.GetPosition() + offset, self.bbox.GetSize())
        self.pos = pcbnew.VECTOR2I(self.pos + offset)
        for net_name in self.pads:
            for i in range(len(self.pads[net_name])):
                self.pads[net_name][i] = pcbnew.VECTOR2I(self.pads[net_name][i] + offset)

class Board:
    def __init__(self, board, ignored_list):
        self.bbox = board.GetBoardEdgesBoundingBox()
        self.footprints = [Footprint(fp, fp.GetReference() in ignored_list) for fp in board.GetFootprints()]
        self.margin = 100

    def mean_footprint_distance(self):
        dist_sum = 0.0
        for fp in self.footprints:
            c = fp.bbox.Centre()
            for fp2 in self.footprints:
                if fp2.ref != fp.ref:
                    c2 = fp2.bbox.Centre()
                    dist_sum += math.sqrt((c.x - c2.x)**2 + (c.y - c2.y)**2)
        return dist_sum / len(self.footprints)

    def closest_paths_len(self):
        len_sum = 0.0
        for fp in self.footprints:
            for net_name in fp.pads:
                min_dist = None
                for pad in fp.pads[net_name]:
                    for fp2 in self.footprints:
                        if fp2.ref == fp.ref:
                            continue
                        if not net_name in fp2.pads:
                            continue
                        for pad2 in fp2.pads[net_name]:
                            dist = math.sqrt((pad.x - pad2.x)**2 + (pad.y - pad2.y)**2)
                            if min_dist is None or min_dist > dist:
                                min_dist = dist
                if min_dist is not None:
                    len_sum += min_dist
        return len_sum

    def step(self):
        eligible = [fp for fp in self.footprints if not fp.is_ignored]
        if len(eligible) == 0:
            return False

        fp = random.choice(eligible)
        min_x = self.bbox.GetX() + self.margin
        min_y = self.bbox.GetY() + self.margin
        max_x = min_x + self.bbox.GetWidth() - fp.bbox.GetWidth() - self.margin
        max_y = min_y + self.bbox.GetHeight() - fp.bbox.GetHeight() - self.margin
        if max_x <= min_x or max_y <= min_y:
            return False

        rand_x = random.randint(min_x, max_x)
        rand_y = random.randint(min_y, max_y)
        rand_pos = pcbnew.VECTOR2I(rand_x, rand_y)
        test_bbox = pcbnew.BOX2I(rand_pos, fp.bbox.GetSize())
        for fp2 in self.footprints:
            if fp2.ref != fp.ref and test_bbox.Intersects(fp2.bbox):
                return False

        # save previous rating and parameters
        #pre_rating = self.mean_footprint_distance()
        pre_rating = self.closest_paths_len()
        offset = rand_pos - fp.bbox.GetPosition()
        fp.shift(offset)
        #post_rating = self.mean_footprint_distance()
        post_rating = self.closest_paths_len()

        # if change introduced worse rating, go back
        if post_rating > pre_rating:
            fp.shift(-offset)
            return False

        return True

    def apply(self, kc_board):
        for fp in self.footprints:
            kc_fp = kc_board.FindFootprintByReference(fp.ref)
            if kc_fp is not None:
                kc_fp.SetPosition(fp.pos)

def delete_tracks_and_vias(board):
    tracks = board.GetTracks()
    to_delete = [t for t in tracks]
    for t in to_delete:
        board.Remove(t)

class PlaceEquallyPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'Place equally'
        self.category = 'Test'
        self.description = 'Plugin that places components equally'
        self.show_toolbar_button = True
        self.icon_file_name = ''

    def Run(self):
        ignored_list = ['J1', 'U3', 'J4', 'J3', 'Y1', 'J2']
        kc_board = pcbnew.GetBoard()
        board = Board(kc_board, ignored_list)
        for i in range(100000):
            board.step()
        board.apply(kc_board)

PlaceEquallyPlugin().register()

