# Trusted geocoding import

BloomAI stores explicit participant latitude/longitude for the executive world map. It does **not** infer coordinates from a country name and it does not silently call a public geocoder during analytics requests.

The supported operational workflow is a reviewed CSV import. A trusted administrator or geocoding process prepares coordinates, records their source, marks each row as verified, runs a dry run, reviews the result, and only then applies the import.

## CSV format

Required columns:

- `latitude`
- `longitude`
- `source`
- `verified`
- either `user_id` or `email`

Optional address columns:

- `address_line1`
- `city`
- `region`
- `postal_code`
- `country`

Example:

```csv
email,latitude,longitude,source,verified,address_line1,city,region,postal_code,country
customer@example.com,0.3476,32.5825,verified-geocoder,true,,Kampala,Central,,Uganda
```

Coordinates must be in the valid WGS84 latitude/longitude ranges. `verified` must be true. The import rejects admin accounts, unknown participants, duplicate participants in one batch, identifier mismatches, unverified rows, and invalid coordinates.

## Dry run first

From `services/marketplace-api`:

```bash
python scripts/import_geocoding.py /path/to/verified_locations.csv
```

Dry-run mode is the default and never changes the database. It reports schema validation failures, unknown participants, duplicate participants, and the number of rows that would be applied.

## Apply reviewed coordinates

After reviewing the dry run:

```bash
python scripts/import_geocoding.py /path/to/verified_locations.csv --apply
```

For each accepted participant, BloomAI stores the supplied latitude/longitude, the source, and the import timestamp. Optional address fields are only replaced when the import explicitly supplies them, so a location import does not erase existing profile data.

## Production use on Railway

Run the command in the marketplace API service environment so it receives the same `DATABASE_URL` as the production API. Keep the CSV outside source control when it contains participant address data. Review access, retention, and handling of address/location data according to your production privacy policy.

This workflow is intentionally geocoding-provider neutral. A future geocoding integration can generate the reviewed CSV, but the application should still preserve the explicit verification step rather than guessing coordinates from country-level data.
