from fontTools.pens.recordingPen import RecordingPen


def get_glyph_path(glyphset, unicode):
    """获取字形的路径描述"""
    glyph = glyphset[unicode]
    pen = RecordingPen()
    glyph.draw(pen)
    path = pen2Path(pen)
    return path


def pen2Path(pen: RecordingPen):
    cmds = []
    crds = []
    for cmd, crd in pen.value:
        cmds.append(cmd)
        crds.append(crd)
    return {"cmds": cmds, "crds": crds}
