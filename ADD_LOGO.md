# Add TARA Logo

## Steps to add your logo:

1. Save your logo image as: `static/tara-logo.png`
2. Recommended size: 50px height (width auto)
3. Format: PNG with transparent background

## Current logo location in code:
- File: `templates/dashboard.html`
- Line: `<img src="/static/tara-logo.png" alt="TARA" style="height: 50px; margin-right: 15px; vertical-align: middle;">`

## If you don't add the logo:
The dashboard will show a broken image icon, but everything else will work fine.

## To add the logo:
```bash
# Copy your logo to the static folder
cp /path/to/your/logo.png /path/to/scalp-bot/static/tara-logo.png

# Or use SCP if on Pi
scp logo.png pi@your-pi:/path/to/scalp-bot/static/tara-logo.png
```

The logo you showed me (star with candlesticks) would look perfect!
