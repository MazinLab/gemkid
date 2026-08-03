import gdstk
from .. import layers
from ..simulate import SonnetMetalLayer, SonnetViaLayer, SonnetPlanarGeneral

ATA_NB = layers.DrawingLayer((0, 0), "aTa_Nb")
HF_GP = layers.DrawingLayer((0, 1), "Hf_Groundplane")
HF_GP_LL = layers.DrawingLayer((0, 2), "Hf_Groundplane_Lincoln_Labs")
TIN_LL = layers.DrawingLayer((10, 0), "TiN_Lincoln_Labs")
HF = layers.DrawingLayer((1, 0), "Hf_Bridge")
HF_LL = layers.DrawingLayer((30, 0), "Hf_Bridge_Lincoln_Labs")
HF_CONTACT = layers.DrawingLayer((20, 0), "Hf_Contact")
HF_CONTACT_LIFTOFF = layers.DrawingLayer((3, 0), "Hf_Contact_Liftoff")
ASI = layers.DrawingLayer((20, 128), "AmorphousSilicon")
ASI_EP = layers.DrawingLayer((20, 129), "AmorphousSilicon_EtchProtect")
GOLD = layers.DrawingLayer((100, 0), "Gold")
MLA_PITCH = layers.DrawingLayer((100, 1), "MLA_Pitch")
MLA_MARK = layers.DrawingLayer((100, 2), "MLA_Mark")
SOLDER_MASK = layers.DrawingLayer((100, 3), "Solder_Mask")

ATA_NB_SONNET = SonnetMetalLayer((0, 0), "atanb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.2878), 105.0)
HF_GP_SONNET = SonnetMetalLayer((0, 1), "hf_gp", 0, SonnetPlanarGeneral(1e-7, 0, 0, 10.0), 150.0)
HF_GP_LL_SONNET = SonnetMetalLayer((0, 2), "hf_gp_ll", 0, SonnetPlanarGeneral(1e-7, 0, 0, 20.0), 200.0)
TIN_LL_SONNET = SonnetMetalLayer((0, 3), "tin_ll", 0, SonnetPlanarGeneral(1e-7, 0, 0, 1.5), 105.0)
HF_SONNET = SonnetMetalLayer((1, 0), "hf", 0, SonnetPlanarGeneral(1e-7, 0, 0, 8.0), 200.0)
HF_LL_SONNET = SonnetMetalLayer((1, 1), "hf_ll", 0, SonnetPlanarGeneral(1e-7, 0, 0, 20.0), 200.0)
HF_VAR_SONNET = SonnetMetalLayer((1, 1), "hf_var", 0, SonnetPlanarGeneral(1e-7, 0, 0, 200.0), 200.0)
TI_GOLD_SONNET = SonnetMetalLayer((99, 0), "tiau", 1, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)

ATA_NB_SONNET_3D = SonnetMetalLayer((0, 0), "atanb", 1, SonnetPlanarGeneral(1e-7, 0, 0, 0.2878), 105.0)
HF_GP_SONNET_3D = SonnetMetalLayer((0, 1), "hf_gp", 1, SonnetPlanarGeneral(1e-7, 0, 0, 10.0), 150.0)
HF_GP_LL_SONNET_3D = SonnetMetalLayer((0, 2), "hf_gp_ll", 1, SonnetPlanarGeneral(1e-7, 0, 0, 20.0), 200.0)
TIN_LL_SONNET_3D = SonnetMetalLayer((0, 3), "tin_ll", 1, SonnetPlanarGeneral(1e-7, 0, 0, 1.5), 105.0)
HF_SONNET_3D = SonnetMetalLayer((1, 0), "hf", 0, SonnetPlanarGeneral(1e-7, 0, 0, 8.0), 200.0)
HF_LL_SONNET_3D = SonnetMetalLayer((1, 1), "hf_ll", 0, SonnetPlanarGeneral(1e-7, 0, 0, 20.0), 200.0)
HF_VAR_SONNET_3D = SonnetMetalLayer((1, 1), "hf_var", 0, SonnetPlanarGeneral(1e-7, 0, 0, 200.0), 200.0)
HF_VIA_SONNET_3D = SonnetViaLayer((2, 0), "hf_via", 0, None, 1)
TI_GOLD_SONNET_3D = SonnetMetalLayer((99, 0), "tiau", 2, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)


def drawing_to_sonnet(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM")
    atanb = [
        p for p in cf.get_polygons() if p.layer == ATA_NB.gds_layer[0] and p.datatype == ATA_NB.gds_layer[1]
    ]
    hf_gp = [
        p for p in cf.get_polygons() if p.layer == HF_GP.gds_layer[0] and p.datatype == HF_GP.gds_layer[1]
    ]
    hf = [p for p in cf.get_polygons() if p.layer == HF.gds_layer[0] and p.datatype == HF.gds_layer[1]]
    hf_gp_ll = [
        p
        for p in cf.get_polygons()
        if p.layer == HF_GP_LL.gds_layer[0] and p.datatype == HF_GP_LL.gds_layer[1]
    ]
    tin_ll = [
        p
        for p in cf.get_polygons()
        if p.layer == TIN_LL.gds_layer[0] and p.datatype == TIN_LL.gds_layer[1]
    ]
    hf_ll = [
        p for p in cf.get_polygons() if p.layer == HF_LL.gds_layer[0] and p.datatype == HF_LL.gds_layer[1]
    ]

    atanb_sim = gdstk.boolean(atanb, atanb, "or", 0.00001, *ATA_NB_SONNET)
    hf_gp_sim = gdstk.boolean(hf_gp, hf_gp, "or", 0.00001, *HF_GP_SONNET)
    hf_gp_ll_sim = gdstk.boolean(hf_gp_ll, hf_gp_ll, "or", 0.00001, *HF_GP_LL_SONNET)
    tin_ll_sim = gdstk.boolean(tin_ll, tin_ll, "or", 0.00001, *TIN_LL_SONNET)
    hf_sim = gdstk.boolean(hf, atanb + tin_ll, "not", 0.00001, *HF_SONNET)
    hf_ll_sim = gdstk.boolean(hf_ll, atanb + tin_ll, "not", 0.00001, *HF_LL_SONNET)
    hf_var = [
        p
        for p in cf.get_polygons()
        if p.layer == HF_VAR_SONNET.gds_layer[0] and p.datatype == HF_VAR_SONNET.gds_layer[1]
    ]

    cell_sim.add(*atanb_sim, *hf_gp_sim, *tin_ll_sim, *hf_sim, *hf_gp_ll_sim, *hf_ll_sim, *hf_var)
    return cell_sim


def drawing_to_sonnet_3d(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM3D")
    atanb = [
        p for p in cf.get_polygons() if p.layer == ATA_NB.gds_layer[0] and p.datatype == ATA_NB.gds_layer[1]
    ]
    hf_gp = [
        p for p in cf.get_polygons() if p.layer == HF_GP.gds_layer[0] and p.datatype == HF_GP.gds_layer[1]
    ]
    hf = [p for p in cf.get_polygons() if p.layer == HF.gds_layer[0] and p.datatype == HF.gds_layer[1]]
    hf_gp_ll = [
        p
        for p in cf.get_polygons()
        if p.layer == HF_GP_LL.gds_layer[0] and p.datatype == HF_GP_LL.gds_layer[1]
    ]
    tin_ll = [
        p
        for p in cf.get_polygons()
        if p.layer == TIN_LL.gds_layer[0] and p.datatype == TIN_LL.gds_layer[1]
    ]
    hf_ll = [
        p for p in cf.get_polygons() if p.layer == HF_LL.gds_layer[0] and p.datatype == HF_LL.gds_layer[1]
    ]
    hf_contact = [
        p
        for p in cf.get_polygons()
        if p.layer == HF_CONTACT.gds_layer[0] and p.datatype == HF_CONTACT.gds_layer[1]
    ]

    atanb_sim = gdstk.boolean(atanb, atanb, "or", 0.00001, *ATA_NB_SONNET_3D)
    hf_gp_sim = gdstk.boolean(hf_gp, hf_gp, "or", 0.00001, *HF_GP_SONNET_3D)
    hf_gp_ll_sim = gdstk.boolean(hf_gp_ll, hf_gp_ll, "or", 0.00001, *HF_GP_LL_SONNET_3D)
    tin_ll_sim = gdstk.boolean(tin_ll, tin_ll, "or", 0.00001, *TIN_LL_SONNET_3D)
    hf_sim = gdstk.boolean(hf, hf, "or", 0.00001, *HF_SONNET_3D)
    hf_ll_sim = gdstk.boolean(hf_ll, hf_ll, "or", 0.00001, *HF_LL_SONNET_3D)
    hf_var = [
        p
        for p in cf.get_polygons()
        if p.layer == HF_VAR_SONNET_3D.gds_layer[0] and p.datatype == HF_VAR_SONNET_3D.gds_layer[1]
    ]
    via_sim = gdstk.boolean(hf, hf_contact, "and", 0.00001, *HF_VIA_SONNET_3D)

    cell_sim.add(*atanb_sim, *hf_gp_sim, *hf_sim, *hf_gp_ll_sim, *hf_ll_sim, *hf_var, *via_sim, *tin_ll_sim)
    return cell_sim
