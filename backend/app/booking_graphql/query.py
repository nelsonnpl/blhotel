"""La query GraphQL completa que Booking usa para "FullSearch", y el mapeo
de accommodationTypeId a nombre legible.

Capturada desde el navegador (F12 -> Network -> Fetch/XHR -> POST a
`booking.com/dml/graphql`). No hace falta entenderla campo a campo, solo
mantenerla actualizada. Ver el docstring de `booking.py` (raíz del proyecto)
para el procedimiento de re-captura si Booking cambia su API.
"""

from __future__ import annotations

GRAPHQL_QUERY = """query FullSearch($input: SearchQueryInput!) {
  searchQueries {
    search(input: $input) {
      ...FullSearchFragment
      __typename
    }
    __typename
  }
}

fragment FullSearchFragment on SearchQueryOutput {
  pagination {
    nbResultsPerPage
    nbResultsTotal
    __typename
  }
  results {
    ...BasicPropertyData
    ...MatchingUnitConfigurations
    ...PropertyBlocks
    priceDisplayInfoIrene {
      ...PriceDisplayInfoIrene
      __typename
    }
    __typename
  }
  __typename
}

fragment BasicPropertyData on SearchResultProperty {
  basicPropertyData {
    accommodationTypeId
    id
    location {
      address
      city
      countryCode
      latitude
      longitude
      __typename
    }
    pageName
    ufi
    photos {
      main {
        highResUrl { relativeUrl __typename }
        __typename
      }
      __typename
    }
    reviewScore: reviews {
      score: totalScore
      reviewCount: reviewsCount
      totalScoreTextTag { translation __typename }
      __typename
    }
    starRating {
      value
      symbol
      __typename
    }
    isClosed
    __typename
  }
  description { text __typename }
  displayName { text __typename }
  location {
    displayLocation
    mainDistance
    beachDistance
    nearbyBeachNames
    isWithinBestLocationScoreArea
    popularFreeDistrictName
    __typename
  }
  mealPlanIncluded { mealPlanType text __typename }
  policies { showFreeCancellation showNoPrepayment __typename }
  __typename
}

fragment MatchingUnitConfigurations on SearchResultProperty {
  matchingUnitConfigurations {
    commonConfiguration {
      name
      unitTypeNames { translation __typename }
      __typename
    }
    unitConfigurations {
      name
      unitTypeNames { translation __typename }
      __typename
    }
    __typename
  }
  __typename
}

fragment PropertyBlocks on SearchResultProperty {
  blocks {
    blockId { roomId occupancy mealPlanId __typename }
    finalPrice { amount currency __typename }
    originalPrice { amount currency __typename }
    onlyXLeftMessage { translation __typename }
    thirdPartyInventoryContext { isTpiBlock __typename }
    freeCancellationUntil
    hasCrib
    blockMatchTags { childStaysForFree __typename }
    __typename
  }
  __typename
}

fragment PriceDisplayInfoIrene on PriceDisplayInfoIrene {
  displayPrice {
    amountPerStay { amount amountRounded currency __typename }
    __typename
  }
  __typename
}
"""


# Mapeo de accommodationTypeId (campo `basicPropertyData.accommodationTypeId`
# del GraphQL) a nombre legible. Booking NO manda el nombre en esta query,
# solo el ID -> hay que traducirlo a mano.
#
# Verificado en vivo (no adivinado) inspeccionando el atributo `ht_id` del
# filtro "Tipo de alojamiento" en searchresults de Madrid y Gran Canaria
# (11-jul-2026). Si aparece un ID que no está aquí, se guarda como
# "Otro (ht_id=<id>)"; para mapearlo, busca "Tipo de alojamiento" en el
# panel de filtros de esa búsqueda y mira el atributo `data-filters-item`
# / `name="ht_id=..."` del checkbox correspondiente en el HTML.
ACCOMMODATION_TYPES: dict[int, str] = {
    201: "Apartamento",
    203: "Albergue",
    204: "Hotel",
    206: "Resort",
    208: "Bed and breakfast",
    210: "Agroturismo",
    212: "Camping resort",
    213: "Villa",
    214: "Camping",
    216: "Hostal / pensión",
    220: "Casa o chalet",
    221: "Lodge",
    222: "Habitación en casa particular",
    223: "Casa rural",
    224: "Tented camp",
    225: "Hotel cápsula",
    226: "Love hotel",
}
