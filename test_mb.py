from services.musicbrainz import search_artist


result = search_artist("Mayhem")

print()
print("TIPO:")
print(type(result))

print()
print("RESULTADO:")
print(result)

print()
print("KEYS:")

if isinstance(result, dict):
    print(result.keys())