import cv2
import mediapipe as mp

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

video = cv2.VideoCapture(0)
video.set(3, 1000)
video.set(4, 780)

# Load images with error checking
img_1 = cv2.imread("circle.png", cv2.IMREAD_UNCHANGED)
img_2 = cv2.imread("circle.png", cv2.IMREAD_UNCHANGED)

# Check if images are loaded
if img_1 is None or img_2 is None:
    print("Error: One or both images could not be loaded.")
    video.release()
    cv2.destroyAllWindows()
    exit()

deg = 0

def position_data(lmlist):
    global wrist, thumb_tip, index_mcp, index_tip, midle_mcp, midle_tip, ring_tip, pinky_tip
    wrist = (lmlist[0][0], lmlist[0][1])
    thumb_tip = (lmlist[4][0], lmlist[4][1])
    index_mcp = (lmlist[5][0], lmlist[5][1])
    index_tip = (lmlist[8][0], lmlist[8][1])
    midle_mcp = (lmlist[9][0], lmlist[9][1])
    midle_tip = (lmlist[12][0], lmlist[12][1])
    ring_tip = (lmlist[16][0], lmlist[16][1])
    pinky_tip = (lmlist[20][0], lmlist[20][1])

def draw_line(p1, p2, size=5):
    cv2.line(img, p1, p2, (50, 50, 255), size)
    cv2.line(img, p1, p2, (255, 255, 255), round(size / 2))

def calculate_distance(p1, p2):
    x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return length

def transparent(targetImg, x, y, size=None):
    if size is not None:
        targetImg = cv2.resize(targetImg, size)

    newFrame = img.copy()

    if targetImg.shape[2] == 4:
        b, g, r, a = cv2.split(targetImg)
        overlay_color = cv2.merge((b, g, r))
        mask = cv2.medianBlur(a, 1)
    else:
        overlay_color = targetImg
        mask = None

    h, w, _ = overlay_color.shape
    roi = newFrame[y:y + h, x:x + w]

    if mask is not None:
        img1_bg = cv2.bitwise_and(roi.copy(), roi.copy(), mask=cv2.bitwise_not(mask))
        img2_fg = cv2.bitwise_and(overlay_color, overlay_color, mask=mask)
        newFrame[y:y + h, x:x + w] = cv2.add(img1_bg, img2_fg)
    else:
        newFrame[y:y + h, x:x + w] = overlay_color

    return newFrame

while True:
    ret, img = video.read()
    img = cv2.flip(img, 1)
    rgbimg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(rgbimg)

    if result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:
            lmList = []
            for id, lm in enumerate(hand.landmark):
                h, w, c = img.shape
                coorx, coory = int(lm.x * w), int(lm.y * h)
                lmList.append([coorx, coory])

            position_data(lmList)
            palm = calculate_distance(wrist, index_mcp)
            distance = calculate_distance(index_tip, pinky_tip)
            ratio = distance / palm

            # If the ratio is lower than a specific value, draw the circle
            if ratio < 1.1:
                centerx = midle_mcp[0]
                centery = midle_mcp[1]
                shield_size = 3.0
                diameter = round(palm * shield_size)
                x1 = round(centerx - (diameter / 2))
                y1 = round(centery - (diameter / 2))

                h, w, c = img.shape
                if x1 < 0:
                    x1 = 0
                elif x1 > w:
                    x1 = w
                if y1 < 0:
                    y1 = 0
                elif y1 > h:
                    y1 = h
                if x1 + diameter > w:
                    diameter = w - x1
                if y1 + diameter > h:
                    diameter = h - y1

                shield_size = diameter, diameter
                ang_vel = 2.0
                deg = deg + ang_vel
                if deg > 360:
                    deg = 0

                hei, wid, col = img_1.shape
                cen = (wid // 2, hei // 2)
                M1 = cv2.getRotationMatrix2D(cen, round(deg), 1.0)
                M2 = cv2.getRotationMatrix2D(cen, round(360 - deg), 1.0)
                rotated1 = cv2.warpAffine(img_1, M1, (wid, hei))
                rotated2 = cv2.warpAffine(img_2, M2, (wid, hei))

                if diameter != 0:
                    img = transparent(rotated1, x1, y1, shield_size)
                    img = transparent(rotated2, x1, y1, shield_size)

    cv2.imshow("Image", img)
    k = cv2.waitKey(1)
    if k == ord('p'):
        break

video.release()
cv2.destroyAllWindows()
