# GEO Metadata Engine

![metadata](https://github.com/user-attachments/assets/da5b4aac-eb68-4a94-b6a9-563bd5c2177a)

Open-source metadata management platform for the WIS-BE project of the Bereich Geoinformation, Amt für Wald und Naturgefahren, Canton of Bern. It provides a structured way to capture, manage, and retrieve geospatial metadata through a web-based admin interface.

GEO Metadata Engine is open-source software, licensed under the [BSD 3-Clause License](LICENSE).

## Key Features

- Manage geospatial metadata (topics, geo packages, layers, attributes, value tables) via a Django admin interface
- Hierarchical data model: Thema → Geopäckli → Ebene / Attribut / Wertetabelle
- Bilingual support (German / French)
- PostgreSQL backend with full migration history

## Development Status

The application is production-ready. The remaining open item is ADFS (Active Directory Federation Services) authentication support.

## Demo

No public demo instance is currently available.

## Contact

The technical contact for GEO Metadata Engine is Pascal Ehrler of the Bereich Geoinformation, Amt für Wald und Naturgefahren, Canton of Bern.

**Project owner:**
Kanton Bern
Amt für Wald und Naturgefahren
Abteilung Fachdienste und Ressourcen
Bereich Geoinformation

## Using GEO Metadata Engine

### Prerequisites

To run this project, we recommend the **conda** package manager.
See [the conda documentation](https://docs.conda.io/en/latest/) for installation instructions.

### Installation

Clone the repository:

```
git clone https://github.com/kanton-bern/geo-metadata-engine.git
cd geo-metadata-engine
```

Create and activate a virtual environment:

```
conda create -n bgi_metadata python=3.14
conda activate bgi_metadata
```

Install dependencies:

```
conda install --yes --file requirements.txt
```

Create a `.env` file in the project root:

```
SECRET_KEY=<your Django secret key>
DEBUG=<True for development, False for production>
DB_HOST=<hostname of your PostgreSQL server>
DB_NAME=<name of your PostgreSQL database>
DB_USER=<PostgreSQL user>
DB_PASSWORD=<PostgreSQL password>
DB_PORT=<PostgreSQL port, typically 5432>
```

Apply migrations and create an admin user:

```
python manage.py migrate
python manage.py createsuperuser
```

Start the development server:

```
python manage.py runserver
```

Open [http://localhost:8000/](http://localhost:8000/) in your browser.

### Docker

A [Dockerfile](./Dockerfile) is available for containerised deployments.

```
# Build the image
docker build -t geo_metadata_engine .

# Run the container
# --network=host is required on Linux so the container can reach the PostgreSQL
# instance running on the host machine (localhost inside the container refers
# to the container itself, not the host).
docker run -d --network=host geo_metadata_engine
```

## Contributing to GEO Metadata Engine

Please read the following documents before contributing:

- [Developer Guidelines](CONTRIBUTING.md)
- [Developer Documentation](CLAUDE.md)

## Contributors

- [Nina Bonassi](https://github.com/nninnja) (Developer)
- [Pascal Ehrler](https://github.com/elpixel-ch) (Product Manager)
- [Hanskaspar Frei](https://github.com/hkfrei) (Initial developer & Architect)

(in alphabetical order)

## Third-Party Licenses

See [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md) for a list of open-source libraries used by this project.
