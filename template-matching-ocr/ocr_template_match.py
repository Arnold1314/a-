# 导入工具包
from imutils import contours
import numpy as np
import argparse
import cv2
import myutils

# 设置参数，argparse用于和命令行之间的交互
#创建解析器
ap = argparse.ArgumentParser()
#添加参数，-i是--image的简写，这里表明是可选参数，意思是如果不选择它那么对应变量会被设置为None，required=True表明这个参数不可缺少。
ap.add_argument("-i", "--image", required=True,
	help="path to input image")
ap.add_argument("-t", "--template", required=True,
	help="path to template OCR-A image")
#ap.parse_args()是解析参数，返回一个对象，对象包含了之前设置的所有参数 ，vars()返回一个字典，字典中包括了解析后对象的属性和属性值
args = vars(ap.parse_args())

# 指定信用卡类型
FIRST_NUMBER = {
	"3": "American Express",
	"4": "Visa",
	"5": "MasterCard",
	"6": "Discover Card"
}
# 绘图展示
def cv_show(name,img):
	cv2.imshow(name, img)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
# 读取一个模板图像，传入的是之前设置的参数
img = cv2.imread(args["template"])
cv_show('img',img)
# 灰度图，颜色转换函数
ref = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)#转换为灰度图
cv_show('ref',ref)
# 二值图像
ref = cv2.threshold(ref, 10, 255, cv2.THRESH_BINARY_INV)[1]#二值化，小于10的像素值赋予255，大于10则为0.
cv_show('ref',ref)

# 计算轮廓
#cv2.findContours()函数接受的参数为二值图，即黑白的（不是灰度图）,cv2.RETR_EXTERNAL只检测外轮廓，cv2.CHAIN_APPROX_SIMPLE只保留终点坐标
#返回的list中每个元素都是图像中的一个轮廓
#找出轮廓，用copy是因为被这个函数会在图像上做修改，以防后面还需继续使用原图像
ref_, refCnts, hierarchy = cv2.findContours(ref.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
#-1表示画所有轮廓，(0,0,255)表示红色，3代表轮廓的粗细
cv2.drawContours(img,refCnts,-1,(0,0,255),3)
cv_show('img',img)
print (np.array(refCnts).shape)
#排序，从左到右，从上到下，[0]表示取得cnt的值
refCnts = myutils.sort_contours(refCnts, method="left-to-right")[0]
digits = {}

# 遍历每一个轮廓
for (i, c) in enumerate(refCnts):
	# 计算外接矩形并且resize成合适大小
	#返回轮廓矩形的坐标和长宽
	(x, y, w, h) = cv2.boundingRect(c)
	roi = ref[y:y + h, x:x + w]
	roi = cv2.resize(roi, (57, 88))
	# 每一个数字对应每一个模板
	digits[i] = roi


# 初始化卷积核
rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
sqKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

#读取输入图像，预处理
image = cv2.imread(args["image"])
cv_show('image',image)
image = myutils.resize(image, width=300)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)##转灰度图
cv_show('gray',gray)

#礼帽操作，突出更明亮的区域
tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, rectKernel) 
cv_show('tophat',tophat) 
#
gradX = cv2.Sobel(tophat, ddepth=cv2.CV_32F, dx=1, dy=0, #ksize=-1相当于用3*3的
	ksize=-1)

gradX = np.absolute(gradX)
(minVal, maxVal) = (np.min(gradX), np.max(gradX))
gradX = (255 * ((gradX - minVal) / (maxVal - minVal)))
gradX = gradX.astype("uint8")

print (np.array(gradX).shape)
cv_show('gradX',gradX)

#通过闭操作（先膨胀，再腐蚀）将数字连在一起
gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectKernel) 
cv_show('gradX',gradX)
#THRESH_OTSU会自动寻找合适的阈值，适合双峰，需把阈值参数设置为0
thresh = cv2.threshold(gradX, 0, 255,
	cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1] 
cv_show('thresh',thresh)
#再来一个闭操作
thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, sqKernel) #再来一个闭操作
cv_show('thresh',thresh)

# 计算轮廓

thresh_, threshCnts, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)

cnts = threshCnts
cur_img = image.copy()
cv2.drawContours(cur_img,cnts,-1,(0,0,255),3) 
cv_show('img',cur_img)
locs = []

# 遍历轮廓
for (i, c) in enumerate(cnts):
	# 计算矩形
	(x, y, w, h) = cv2.boundingRect(c)
	#矩形的比例
	ar = w / float(h)

	# 选择合适的区域，根据实际任务来，这里的基本都是四个数字一组，宽比高在需要范围内，并且宽和高也要在指定范围
	if ar > 2.5 and ar < 4.0:

		if (w > 40 and w < 55) and (h > 10 and h < 20):
			#符合的留下来
			locs.append((x, y, w, h))

# 将符合的轮廓从左到右排序，根据x大小来排
locs = sorted(locs, key=lambda x:x[0])
output = []

# 遍历每一个轮廓中的数字
for (i, (gX, gY, gW, gH)) in enumerate(locs):
	# initialize the list of group digits
	groupOutput = []

	# 根据坐标提取每一个组
	group = gray[gY - 5:gY + gH + 5, gX - 5:gX + gW + 5]
	cv_show('group',group)
	# 预处理
	group = cv2.threshold(group, 0, 255,
		cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
	cv_show('group',group)
	# 计算每一组的轮廓
	group_,digitCnts,hierarchy = cv2.findContours(group, cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	digitCnts = contours.sort_contours(digitCnts,
		method="left-to-right")[0]

	# 计算每一组中的每一个数值
	for c in digitCnts:
		# 找到当前数值的轮廓，resize成合适的的大小
		(x, y, w, h) = cv2.boundingRect(c)
		roi = group[y:y + h, x:x + w]
		roi = cv2.resize(roi, (57, 88))
		cv_show('roi',roi)

		# 计算匹配得分
		scores = []

		# 在模板中计算每一个得分，与十个模板匹配得到最大分数
		for (digit, digitROI) in digits.items():
			# 模板匹配
			result = cv2.matchTemplate(roi, digitROI,
				cv2.TM_CCOEFF)
			#拿出匹配后的最大值
			(_, score, _, _) = cv2.minMaxLoc(result)
			scores.append(score)

		# 得到最合适的数字
		groupOutput.append(str(np.argmax(scores)))#np.argmax() 返回的是最大值的索引，这个最大值就是匹配上的数字
	# 画出来
	#画出框
	cv2.rectangle(image, (gX - 5, gY - 5),
		(gX + gW + 5, gY + gH + 5), (0, 0, 255), 1)
	#加上对应数字
	cv2.putText(image, "".join(groupOutput), (gX, gY - 15),
		cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

	# 得到结果
	output.extend(groupOutput)

# 打印结果
print("Credit Card Type: {}".format(FIRST_NUMBER[output[0]]))
print("Credit Card #: {}".format("".join(output)))
cv2.imshow("Image", image)
cv2.waitKey(0)