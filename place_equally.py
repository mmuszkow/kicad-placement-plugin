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

        # bring back the defaults
        fp.Reference().SetVisible(ref_visible)
        fp.Value().SetVisible(val_visible)
        fp.InvalidateGeometryCaches()

class Solution:
    def __init__(self):
        self.edge_cuts = []
        self.bbox = None
        self.front = []
        self.back = []

    def randomize_all(self):
        pass

    def create_new(self):
        pass

    def is_valid(self):
        if len(self.edge_cuts) == 0 or self.bbox == None:
            return False

        if len(self.front) == 0 and len(self.back) == 0:
            return False

        for footprint in self.front:
            if footprint.is_ignored:
                continue

            if not self.bbox.Contains(footprint.bbox):
                debug(f'{footprint.ref} not in board bbox')
                return False
            
            for footprint2 in self.front:
                if footprint2.ref == footprint.ref:
                    continue
                if footprint.bbox.Intersects(footprint2.bbox):
                    debug(f'{footprint.ref} intersects {footprint2.ref}')
                    return False

        for footprint in self.back:
            if footprint.is_ignored:
                continue

            if not self.bbox.Contains(footprint.bbox):
                debug(f'{footprint.ref} not in board bbox')
                return False
            
            for footprint2 in self.back:
                if footprint2.ref == footprint.ref:
                    continue
                if footprint.bbox.Intersects(footprint2.bbox):
                    debug(f'{footprint.ref} intersects {footprint2.ref}')
                    return False

        return True

def solution_from_board(board):
    solution = Solution()
    ignored_list = ['J1', 'U3', 'J4', 'J3']
    solution.edge_cuts = [d for d in board.GetDrawings() if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() == pcbnew.Edge_Cuts]
    
    min_x = min([s.GetBoundingBox().GetX() for s in solution.edge_cuts])
    min_y = min([s.GetBoundingBox().GetY() for s in solution.edge_cuts])
    max_x = max([s.GetBoundingBox().GetX() + s.GetBoundingBox().GetWidth() for s in solution.edge_cuts])
    max_y = max([s.GetBoundingBox().GetY() + s.GetBoundingBox().GetHeight() for s in solution.edge_cuts])
    solution.bbox = pcbnew.BOX2I(pcbnew.VECTOR2I(min_x, min_y), pcbnew.VECTOR2I(max_x - min_x, max_y - min_y))

    for footprint in board.GetFootprints():
        layer = footprint.GetLayer()
        is_ignored = footprint.GetReference() in ignored_list
        if layer == pcbnew.F_Cu:
            solution.front.append(Footprint(footprint, is_ignored))
        elif layer == pcbnew.B_Cu:
            solution.back.append(Footprint(footprint, is_ignored))

    return solution

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
        board = pcbnew.GetBoard()
        solution = solution_from_board(board) 
        wx.MessageBox(self.name, f'is_valid: {solution.is_valid()}')

PlaceEquallyPlugin().register()

