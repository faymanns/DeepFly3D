import numpy as np

from .cv_util import triangulate_linear
from . import skeleton

def energy_drosoph(cam_list, img_id, j_id, points2d, points3d=None, bone_length=None, image_shape=[960,480], hm_shape=(64,128)):
    """
    calculate energy from 2d observations
    points2d: 2x3 array, observations from three cameras
    points3d: 15x3 array, used only to calculate the bone probability
    """
    points2d_list = [p_.reshape(1, 2) for p_ in points2d*image_shape]
    p3d = triangulate_linear(cam_list, points2d_list)

    err_proj = error_reprojection(cam_list, (points2d*image_shape).astype(int))
    err_proj = np.mean(np.abs(err_proj))

    prob_heatm = probability_heatmap(cam_list, img_id, j_id, (points2d*hm_shape).astype(int))

    # not the root of the chain
    prob_bone = None
    '''
    if bone_length is not None:
        target = np.sqrt(np.sum(np.power(points3d[j_id+1]-points3d[j_id],2)))
        print("Bone length constraint: {} {}".format(target, bone_length[j_id]))
        prob_bone = prob_bone_length(target=target, known_length=bone_length[j_id])
    else:
        prob_bone = None
    '''
    return p3d, err_proj, prob_heatm, prob_bone

def prob_from_heatmap(hm, p, eps=0.1):
    '''
    points2d: pixel space
    hm: probability map in full image size, pixel space
    '''
    prob = eps
    if not(p[1] >= hm.shape[0]  or p[0] >= hm.shape[1] or p[0]<0 or p[1]<0):
        prob += hm[p[1], p[0]]
    return prob


def probability_heatmap(cam_list, img_id, j_id, points2d, image_shape=(480,960)):
    hm_list = [cam.get_heatmap(img_id, j_id) for cam in cam_list]

    prob = 1
    for hm, p in zip(hm_list, points2d):
        prob *= prob_from_heatmap(hm, p)
    return prob

def error_reprojection(cam_list, points2d):
    '''
    points2d: nx2 array containing projections
    '''
    points2d_list = [p.reshape(1,2) for p in points2d]
    point3d = triangulate_linear(cam_list, points2d_list)

    err = list()
    for cam, p in zip(cam_list, points2d):
        err.append(cam.project(point3d)-p)
    return np.array(err)


def project_on_last(cam_list, p):
    p = [p_.reshape(1,2) for p_ in p]

    point3d = triangulate_linear(cam_list[:-1], p)
    point2d = cam_list[-1].project(point3d)
    point2d = np.squeeze(point2d)
    return point2d


def calc_bone_length(p):
    p = np.squeeze(p)
    print(p.shape)
    bone_length = np.zeros(p.shape[0], dtype=float)
    for j in range(p.shape[0]-1):
        bone_length[j] = np.sqrt(np.sum(np.power(p[j]-p[j+1], 2), axis=1))
    return bone_length


def d_ij(p3d_c, p3d_p, param):
        dist = np.linalg.norm((p3d_p-p3d_c))
        mu, sig = param
        return np.exp(-np.power(dist - mu, 2.) / (2 * np.power(sig, 2.)))


def err_planarity(points3d):
    points3d = np.delete(points3d, np.where(points3d==0))
    A = np.c_[data[:,0], data[:,1], np.ones(data.shape[0])]
    C,_,res,_ = scipy.linalg.lstsq(A, data[:,2])    # coefficients
    return np.max(np.abs(res))
