# Word Add-in (Sideload, No Backend)

## Dev server (HTTPS localhost)
```bash
cd taskpane
npm i
npm run dev
# visit https://localhost:5173 (accept self-signed cert)
```

## Sideload the add-in
### Word on the web
Insert → Office Add-ins → **Upload My Add-in** → select `addin/manifest.xml`

### Word desktop
Insert → Office Add-ins → **Upload My Add-in** (or use a shared/network catalog if the button is unavailable).

## Update origin
If you change the port/host, update URLs in `addin/manifest.xml` to match your dev server.
