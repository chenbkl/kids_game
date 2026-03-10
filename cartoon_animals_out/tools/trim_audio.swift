import AVFoundation
import Foundation

enum TrimError: Error {
    case usage
    case badStart
    case badDuration
}

let args = CommandLine.arguments
guard args.count == 5 else {
    throw TrimError.usage
}

let inputURL = URL(fileURLWithPath: args[1])
let outputURL = URL(fileURLWithPath: args[2])
guard let startSeconds = Double(args[3]), startSeconds >= 0 else {
    throw TrimError.badStart
}
guard let durationSeconds = Double(args[4]), durationSeconds > 0 else {
    throw TrimError.badDuration
}

let inputFile = try AVAudioFile(forReading: inputURL)
let format = inputFile.processingFormat
let sampleRate = format.sampleRate
let startFrame = AVAudioFramePosition(startSeconds * sampleRate)
let requestedFrames = AVAudioFramePosition(durationSeconds * sampleRate)
let availableFrames = max(0, inputFile.length - startFrame)
let framesToCopy = min(requestedFrames, availableFrames)

inputFile.framePosition = startFrame

let outputFile = try AVAudioFile(
    forWriting: outputURL,
    settings: format.settings,
    commonFormat: format.commonFormat,
    interleaved: format.isInterleaved
)

var remaining = framesToCopy
let chunkSize: AVAudioFrameCount = 4096

while remaining > 0 {
    let frameCount = AVAudioFrameCount(min(AVAudioFramePosition(chunkSize), remaining))
    guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else {
        break
    }

    try inputFile.read(into: buffer, frameCount: frameCount)
    if buffer.frameLength == 0 {
        break
    }

    try outputFile.write(from: buffer)
    remaining -= AVAudioFramePosition(buffer.frameLength)
}
