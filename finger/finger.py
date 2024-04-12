import os
import id3finger

print("------------------")
print("id3 Finger Toolkit")
print("------------------")

# Before calling any function of the SDK you must first check a valid license file.
# To get such a file please use the provided activation tool.
# It is also possible to use the FingerLicense.Activation(...) APIs

def face(image_path_1, image_path_2) -> bool:
    cw = os.getcwd()
    id3finger.FingerLicense.check_license("./id3Finger.lic")

    has_matched = False

    # The Finger SDK heavily relies on deep learning technics and hence requires trained models to run.
    # Fill in the correct path to the downloaded models.
    modelPath = "./models"

    # Once a model is loaded in the desired processing unit (CPU or GPU) several instances of the associated processor can be created.
    # For instance in this sample, we load:
    # - a minutia detector to extract iso minutiae data (mandatory)
    # - a fingerprint aligner and encoder to extract proprietary template data for better accuracy (optional)
    print("Loading models... ")
    id3finger.FingerLibrary.load_model(
        modelPath, 
        id3finger.FingerModel.FINGER_MINUTIA_DETECTOR_3B, 
        id3finger.ProcessingUnit.CPU
    ) # mandatory
    id3finger.FingerLibrary.load_model(
        modelPath, 
        id3finger.FingerModel.FINGER_ALIGNER_1A, 
        id3finger.ProcessingUnit.CPU
    ) # optional if using proprietary data
    id3finger.FingerLibrary.load_model(
        modelPath, 
        id3finger.FingerModel.FINGER_ENCODER_1A, 
        id3finger.ProcessingUnit.CPU
    ) # optional if using proprietary data
    print("Done.")

    # Load sample images from files.
    # Finger images are always loaded to 8 bits grayscale pixel format
    #
    print("Loading images from files... ")
    image1 = id3finger.FingerImage.from_file(
        image_path_1, 
        id3finger.PixelFormat.GRAYSCALE_8_BITS
    )
    image2 = id3finger.FingerImage.from_file(
        image_path_2, 
        id3finger.PixelFormat.GRAYSCALE_8_BITS
    )
    print("Done.")

    # Set the resolution of the two previsously loaded finger images.
    # Not doing so would result in a -2006 "Invalid resolution" error during finger template extraction
    # id3 Finger SDK processors uses only 500 dpi images. Images with a different resolution must be rescaled
    # before use.
    # Note: the setResolution method set both the vertical and the horizontal resolutions values at the same time.
    image1.set_resolution(500)
    image2.set_resolution(500)

    # To use the finger minutia detector it is required to instanciate a finger extractor module and 
    # then load the required model files into the memory of the desired processing unit.
    # 
    # Minutia detection is mandatory and is self-sufficient for creating iso templates.
    # Setting other models will activate the generation of additional proprietary template data. See 
    # SDK user guide for more details.
    print("Init finger extractor... ")
    fingerExtractor = id3finger.FingerExtractor(
        finger_aligner_model = id3finger.FingerModel.FINGER_ALIGNER_1A, # activate alignment for finger encoding (optional)
        finger_encoder_model = id3finger.FingerModel.FINGER_ENCODER_1A, # activate proprietary template encoding (optional)
        thread_count = 4)
    print("Done.")

    # Create the templates from each image.
    # As we activated proprietary encoding it will be processed at the same time
    print("Creating templates... ")
    referenceTemplate = fingerExtractor.create_template(image1)
    probeTemplate = fingerExtractor.create_template(image2)
    print("Done.")

    # Initialize a finger matcher instance.
    fingerMatcher = id3finger.FingerMatcher()

    # The matching process returns a score between 0 and 65535. To take a decision this score
    # must be compared to a defined threshold.
    # For 1 to 1 authentication, it is recommended to select a threshold of at least 4000 (FMR=1:10K).
    # Please see documentation to get more information on how to choose the threshold.
    print("Comparing templates... ")
    score = fingerMatcher.compare_templates(referenceTemplate, probeTemplate)
    print("Done.")
    if score > id3finger.FingerMatcherThreshold.FMR10000:
        print(f"Match (minutiae and proprietary): {score}")
    else:
        print(f"No match (minutiae and proprietary): {score}")

    # By default the Finger Matcher instance uses all possible data found in the provided templates.
    # Here for exemple it uses both the ISO minutiae data and the proprietary encoded template
    # 
    # However it is possible to force it to only use ISO minutiae data as such.
    fingerMatcher.minex_only = True

    print("Comparing templates minutiae only... ")
    scoreMinex = fingerMatcher.compare_templates(referenceTemplate, probeTemplate)
    print("Done.")

    if scoreMinex > id3finger.FingerMatcherThreshold.FMR10000:
        has_matched = True
        print(f"Match (minutiae only): {scoreMinex}")
    else:
        print(f"No match (minutiae only): {scoreMinex}")

    # Closing all SDK ressources
    del image1
    del image2
    del fingerMatcher
    del fingerExtractor
    id3finger.FingerLibrary.unload_model(
        id3finger.FingerModel.FINGER_ALIGNER_1A, 
        id3finger.ProcessingUnit.CPU
    )
    id3finger.FingerLibrary.unload_model(
        id3finger.FingerModel.FINGER_ENCODER_1A, 
        id3finger.ProcessingUnit.CPU
    )
    id3finger.FingerLibrary.unload_model(
        id3finger.FingerModel.FINGER_MINUTIA_DETECTOR_3B, 
        id3finger.ProcessingUnit.CPU
    )
    print("Sample terminated successfully.")

    return has_matched