import pcbnew
import random
import wx

def debug(msg):
    wx.MessageBox(msg, 'debug')

class Footprint:
    def __init__(self, fp, is_ignored = False):
        self.is_ignored = is_ignored

        # we want bounding box without labels
        ref_visible = fp.Reference().IsVisible()
        val_visible = fp.Value().IsVisible()
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.InvalidateGeometryCaches()

        self.ref = fp.GetReference()
        self.pos = pcbnew.VECTOR2I(fp.GetPosition())
        fbbox = fp.GetBoundingBox()
        self.bbox = pcbnew.BOX2I(fbbox.GetPosition(), fbbox.GetSize())
        self.layer = fp.GetLayer()

        # bring back the defaults
        fp.Reference().SetVisible(ref_visible)
        fp.Value().SetVisible(val_visible)
        fp.InvalidateGeometryCaches()

    def is_valid_placement(self, board):
        if self.is_ignored:
            return True

        if not board.bbox.Contains(self.bbox):
            return False

        for footprint in board.footprints:
            if footprint.ref == self.ref:
                continue

            if footprint.bbox.Intersects(self.bbox):
                return False

            #if footprint.bbox.Contains(self.bbox):
            #    return False

        return True

    def apply(self, kc_board):
        fp = kc_board.FindFootprintByReference(self.ref)
        if fp is not None:
            fp.SetPosition(self.pos)

class Board:
    def __init__(self, board, ignored_list):
        self.bbox = board.GetBoardEdgesBoundingBox()
        self.footprints = [Footprint(fp, fp.GetReference() in ignored_list) for fp in board.GetFootprints()]
        self.margin = 100

    def try_move_random(self):
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

        offset = rand_pos - fp.bbox.GetPosition()
        fp.bbox = test_bbox
        fp.pos += offset
        return True

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
        ignored_list = ['J1', 'U3', 'J4', 'J3']
        kc_board = pcbnew.GetBoard()
        board = Board(kc_board, ignored_list)
        for i in range(100):
            board.try_move_random()
        for fp in board.footprints:
            fp.apply(kc_board)

PlaceEquallyPlugin().register()

