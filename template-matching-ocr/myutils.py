import cv2

def sort_contours(cnts, method="left-to-right"):#先给method一个默认值
    reverse = False
    i = 0

    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1
    boundingBoxes = [cv2.boundingRect(c) for c in cnts] #用一个最小的矩形，把找到的形状包起来返回起始点x,y和长宽h,w的列表
    (cnts, boundingBoxes) = zip(
        *sorted(
            zip(cnts, boundingBoxes),#zip函数将cnt和boundingBoxes打包成列表
            key=lambda b: b[1][i],#1代表根据boundingBox中的值，i在这个例子中为0，代表按x排序
            reverse=reverse))#reverse为False是升序

    return cnts, boundingBoxes
def resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)#算出height占原图h的比例
        dim = (int(w * r), height)#算出宽，再和height作为元组
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    resized = cv2.resize(image, dim, interpolation=inter)#最后一个参数是插值方法
    return resized