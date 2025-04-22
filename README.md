## Usage

### 1. Create Content

Place your markdown scripts in the `scripts/` directory:
```markdown
# scripts/script_001.md
Your video content here...
```

### 2. Generate Audio

```bash
python pipeline/text_to_speech.py
```

### 3. Create Video

```bash
python pipeline/make_video.py
```

### 4. Upload to YouTube

```bash
python pipeline/upload_video.py
```

### 5. Track Statistics

```bash
python pipeline/track_video_stats.py
```

## Configuration

### Video Settings
- Video dimensions: 1080x1920 (vertical format)
- Frame rate: 24 fps
- Codec: H.264
- Audio codec: AAC

### Thumbnail Settings
- Generated using DALL-E 3
- Size: 1024x1024 (resized to 1080x1920)
- Custom text overlay

### YouTube Settings
- Category: Science & Technology
- Default privacy: Public
- Tags: AI, PDF, GPT-4, YouTube Shorts, Try This AI

## Error Handling

The pipeline includes comprehensive error handling for:
- Missing API keys
- File not found errors
- API rate limits
- Upload failures
- Authentication issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here]

## Support

For support, please [open an issue](your-issues-url) or contact [your-email].
