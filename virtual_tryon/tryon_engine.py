import cv2
import mediapipe as mp
import numpy as np

class TryOnEngine:
    def __init__(self):
        """
        Initializes the Try-On Engine with Mediapipe Pose.
        """
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5)
        print("TryOnEngine initialized.")

    def apply_tryon(self, user_image_path, clothing_image_path, output_path):
        """
        Applies a piece of clothing to a user's photo.

        :param user_image_path: Path to the user's image.
        :param clothing_image_path: Path to the clothing item's image (PNG with transparency).
        :param output_path: Path to save the resulting image.
        """
        # 1. Load images
        user_img = cv2.imread(user_image_path)
        clothing_img = cv2.imread(clothing_image_path, cv2.IMREAD_UNCHANGED)

        if user_img is None or clothing_img is None:
            print("Error: Could not load one or both images.")
            return

        # 2. Detect pose
        # Convert the BGR image to RGB.
        rgb_user_img = cv2.cvtColor(user_img, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_user_img)

        if not results.pose_landmarks:
            print("Error: Could not detect pose landmarks in the user image.")
            return

        landmarks = results.pose_landmarks.landmark
        h, w, _ = user_img.shape
        print("Successfully detected pose landmarks.")

        # 3. Calculate transformation
        # Get coordinates of key landmarks for the torso
        left_shoulder = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].x * w, landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].y * h]
        right_shoulder = [landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value].x * w, landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value].y * h]
        left_hip = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].x * w, landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].y * h]
        right_hip = [landmarks[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value].x * w, landmarks[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value].y * h]

        # Define the destination quadrilateral on the user's body.
        # This is a simplified model for a t-shirt, mapping its corners to the user's torso.
        dst_points = np.array([left_shoulder, right_shoulder, right_hip, left_hip], dtype="float32")

        # Source points are the corners of the clothing image.
        # Assuming the clothing image is a flat, frontal view of the item.
        cloth_h, cloth_w, _ = clothing_img.shape
        src_points = np.array([[0, 0], [cloth_w, 0], [cloth_w, cloth_h], [0, cloth_h]], dtype="float32")

        # Calculate the perspective transformation matrix
        M = cv2.getPerspectiveTransform(src_points, dst_points)
        print("Calculated perspective transformation matrix.")

        # 4. Warp clothing
        # Warp the clothing image to fit the user's torso
        warped_clothing = cv2.warpPerspective(clothing_img, M, (w, h))
        print("Warped clothing image.")

        # 5. Overlay and blend
        # Create a mask from the alpha channel of the warped clothing image
        alpha_channel = warped_clothing[:, :, 3]
        mask = alpha_channel > 0

        # To blend, we can convert the boolean mask to a 3-channel image
        # where the mask is 1 (or 255) and the rest is 0.
        mask_3_channel = np.zeros_like(user_img)
        for i in range(3):
            mask_3_channel[:,:,i] = mask

        # Black out the area of the clothing on the user image
        torso_region = cv2.bitwise_and(user_img, cv2.bitwise_not(mask_3_channel))

        # Isolate the clothing from the warped image (without alpha channel)
        warped_clothing_bgr = warped_clothing[:, :, :3]
        clothing_region = cv2.bitwise_and(warped_clothing_bgr, mask_3_channel)

        # Add the two images together to get the final result
        final_img = cv2.add(torso_region, clothing_region)
        print("Overlayed and blended images.")

        # 6. Save result
        cv2.imwrite(output_path, final_img)
        print(f"Saved final image to {output_path}")

    def __del__(self):
        """
        Cleans up the Mediapipe Pose object.
        """
        self.pose.close()

if __name__ == '__main__':
    # --- Example Usage ---
    # To run this script, you need to provide paths to a user image and a clothing image.
    # The clothing image should be a PNG with a transparent background.

    # try:
    #     engine = TryOnEngine()

    #     user_image_path = 'path/to/your/user_image.jpg'
    #     clothing_image_path = 'path/to/your/clothing_item.png'
    #     output_image_path = 'path/to/your/output_image.jpg'

    #     engine.apply_tryon(user_image_path, clothing_image_path, output_image_path)
    # finally:
    #      # Ensure the engine's resources are cleaned up
    #     if 'engine' in locals() and isinstance(engine, TryOnEngine):
    #         engine.pose.close()

    print("Virtual Try-On Engine script. Provide image paths in the main block to run the engine.")
