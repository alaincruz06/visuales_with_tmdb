import tmdbsimple as tmdb
from datetime import date
import pandas as pd
import random


def leaveJustForeignMovies():
    # Encuentra la carpeta de Peliculas Extranjeras y borra todo lo que esta antes de ella
    # Encuentra la carpeta de Peticiones y borra todo lo que esta despues de ella
    # La ruta suele ser: root/Peliculas/Extranjeras
    # La ruta suele ser: root/Peticiones
    with open("listado.txt", "r", encoding="utf8") as file:
        lines = file.readlines()
        extranjeras_index = None
        peticiones_index = None

        for i, line in enumerate(lines, start=1):
            if "Extranjeras" in line:
                extranjeras_index = i - 1
            elif "├── Peticiones" in line:
                peticiones_index = i - 1

        if extranjeras_index is not None and peticiones_index is not None:
            lines = lines[extranjeras_index:peticiones_index]
            with open("listado.txt", "w", encoding="utf8") as file:
                file.writelines(lines)
    print("Listo leaveJustForeignMovies!")


def cleanIndentSignsAndWhiteSpaces():
    """Elimina los signos de indentación y los espacios en blanco del listado de películas"""
    with open("listado.txt", "r+", encoding="utf8") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            lines[i] = (
                line.lstrip()
                .replace("│\xa0\xa0", "")
                .replace("├──", "")
                .replace("└──", "")
            )
            lines[i] = lines[i].lstrip()
        file.seek(0)
        file.writelines(lines)
        file.truncate()
    print("Listo cleanIndentSignsAndWhiteSpaces!")


def removeSubsFolders():
    """Elimina las carpetas de subtítulos del listado de películas"""
    with open("listado.txt", "r+", encoding="utf8") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            lines[i] = line.lstrip().replace("Subs\n", "")
        file.seek(0)
        file.writelines(lines)
        file.truncate()
    print("Listo removeSubsFolders!")


def filterByYear():
    """Permite filtrar por año según entrada del usuario"""
    first_available_year: str = ""
    with open("listado.txt", "r", encoding="utf8") as file:
        lines = file.readlines()
        while first_available_year == "":
            for line in lines:
                if line.replace("\n", "").isdigit():
                    first_available_year = line
                    break
    input_first_year = input(
        f"Introduce el año inicial a filtrar (Se puede dejar en blanco - Primer año en listado: {first_available_year}): "
    )
    input_last_year = input(
        "Introduce el año final a filtrar (Se puede dejar en blanco): "
    )
    with open("listado.txt", "r", encoding="utf8") as file:
        lines = file.readlines()
        for line in lines:
            if not input_first_year:
                # Obtiene el primer año si no se introduce un año inicial
                if "Extranjeras" in line:
                    next_line_index = lines.index(line) + 1
                    while next_line_index < len(lines):
                        next_line = lines[next_line_index]
                        if next_line.strip().isdigit():
                            input_first_year = next_line.strip()
                            break
                        next_line_index += 1
            if not input_last_year:
                # Obtiene el año actual si no se introduce un año final
                current_date = date.today()
                input_last_year = str(current_date.year)
    if input_first_year > input_last_year:
        print("Error filtrando, el año inicial debe ser menor o igual al año final")
        return [False, (input_first_year, input_last_year)]
    else:
        print(
            "Filtrando películas extranjeras desde el "
            + input_first_year
            + " hasta el "
            + input_last_year
        )
        return [True, (input_first_year, input_last_year)]


def filterMovies(input_first_year: str, input_last_year: str):
    """Filtra del listado de películas SOLO las que se incluyan eliminando el resto del listado"""
    with open("listado.txt", "r", encoding="utf8") as file:
        lines = [line.replace("\n", "").strip() for line in file.readlines()]
        filtered_movies = []
        # Si son años diferentes entonces hay rango
        if input_first_year != input_last_year:
            filtered_movies = lines[
                lines.index(input_first_year) + 1 : lines.index(input_last_year)
            ]
        # Es el mismo año, así que solo películas de ese año
        else:
            next_index: int
            for i in lines[lines.index(input_first_year) + 1 : len(lines)]:
                if not i:
                    break
                elif i.isdigit() and int(i) == int(input_first_year) + 1:
                    break
                else:
                    filtered_movies.append(i)
        print("Películas filtradas: " + str(filtered_movies))

        # Generate list of all possible years between input_first_year and input_last_year
        years_in_range = [
            str(year) for year in range(int(input_first_year), int(input_last_year) + 1)
        ]

        return (filtered_movies, years_in_range)


def removeYearsInTitles(filteredMovies: list, yearsInRange: list):
    # check if whats between those chars "(" and "_" is
    # Indice para llevar cuenta de los años en rango
    i: int = 0
    currentYear: int = yearsInRange[i]
    cleanedMovieTitles: list = []
    for movieTitle in filteredMovies:
        try:
            if movieTitle[:4].isdigit() and movieTitle[4] == "_":
                cleanedMovieTitles.append(movieTitle[5:])
            elif (
                movieTitle.endswith(")")
                and movieTitle[
                    movieTitle.rfind("(") + 1 : movieTitle.rfind(")")
                ].isdigit()
            ):

                cleanedMovieTitles.append(movieTitle[:-7])
            else:
                cleanedMovieTitles.append(movieTitle)
                continue
        except IndexError as ie:
            cleanedMovieTitles.append(movieTitle)
            continue
    print("Listo removeYearsInTitles!")
    return list(dict.fromkeys(cleanedMovieTitles))


def checkMoviesOnTMDB(filteredMovies: list, yearsInRange: list):
    """Comprueba con el listado de películas filtradas su equivalente en la API de TMDB"""
    # Usa tu propia Api-key
    tmdb.API_KEY = "TU_API_KEY"
    timeoutRandomizer: int = random.randrange(1, 5)
    # segundos de timeout - no queremos crear spam
    tmdb.REQUESTS_TIMEOUT = timeoutRandomizer
    search = tmdb.Search()
    moviesWithInfo: dict = {}
    for movieTitle in filteredMovies:
        # Indice para llevar cuenta de los años en rango
        i: int = 0
        currentYear: int = yearsInRange[i]
        if movieTitle == int(currentYear) + 1:
            i = i + 1
            break
        else:
            # Busca la pelicula con el año del filtro
            response: dict = search.movie(
                query=movieTitle,
            )
            movies: list = response["results"]
            movie_dict = None
            for moviedict in movies:
                release_year = moviedict.get("release_date", "")[:4]
                if release_year:
                    if abs(int(release_year) - int(currentYear)) <= 5:
                        movie_dict = moviedict
                        break
            if not movie_dict:
                print(
                    "No se encontró la película: "
                    + movieTitle
                    + " currentYear: "
                    + str(currentYear)
                )
            else:
                # Actualizando imagenes con url de la API
                movie_dict["backdrop_path"] = (
                    "https://image.tmdb.org/t/p/original/" + movie_dict["backdrop_path"]
                )
                moviesWithInfo[moviedict["title"]] = movie_dict

    queryData: pd.DataFrame = pd.DataFrame.from_dict(moviesWithInfo)
    queryData = queryData.transpose()
    queryData.to_excel("filtered_movies.xlsx", sheet_name="movies", index=False)
    print(queryData)


leaveJustForeignMovies()
cleanIndentSignsAndWhiteSpaces()
removeSubsFolders()
shouldFilter: list = filterByYear()
if shouldFilter:
    filteredMoviesAndYears: tuple = filterMovies(shouldFilter[1][0], shouldFilter[1][1])
    filteredMovies: list = removeYearsInTitles(
        filteredMoviesAndYears[0], filteredMoviesAndYears[1]
    )
    checkMoviesOnTMDB(filteredMovies, filteredMoviesAndYears[1])
