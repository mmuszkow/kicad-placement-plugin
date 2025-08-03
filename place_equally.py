import pcbnew
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

        other = []
        if self.layer == pcbnew.F_Cu:
            other = board.front
        elif self.layer == pcbnew.B_Cu:
            other = board.back

        for footprint in other:
            if footprint.ref == self.ref:
                continue

            if footprint.bbox.Intersects(self.bbox):
                return False

            if footprint.bbox.Contains(self.bbox):
                return False

        return True

class Board:
    def __init__(self, board, ignored_list):
        self.bbox = board.GetBoardEdgesBoundingBox()
        self.front = []
        self.back = []
        for footprint in board.GetFootprints():
            layer = footprint.GetLayer()
            is_ignored = footprint.GetReference() in ignored_list
            if layer == pcbnew.F_Cu:
                self.front.append(Footprint(footprint, is_ignored))
            elif layer == pcbnew.B_Cu:
                self.back.append(Footprint(footprint, is_ignored))

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
        board = pcbnew.GetBoard()
        b = Board(board, ignored_list)

PlaceEquallyPlugin().register()

