# Railway Deployment Notes

## Deployment Timing
- **Railway deployments take approximately 2 minutes to complete**
- Do NOT attempt to wait with sleep commands - they are always too short
- Wait for user confirmation that deployment is complete before testing API changes
- Previous incorrect assumptions: 30 seconds, 1 minute - all too short

## Deployment Process
1. Push changes to GitHub
2. Railway automatically triggers deployment
3. **WAIT FOR USER CONFIRMATION** - do not test APIs until confirmed
4. Only then test the updated backend endpoints

## Key Endpoints
- Production backend: `https://smooth-mailbox-production.up.railway.app`
- API base: `https://smooth-mailbox-production.up.railway.app/api/v1`
- Requires header: `X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I`

