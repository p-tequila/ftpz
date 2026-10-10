"""Four immutable encrypted owner objects, bound by the approved request hash."""
SITES = tuple(f"site-{letter}" for letter in "abcd")
LAYOUT = "four-encrypted-silos-v1"


def split_silos(envelope):
    request = dict(envelope["request"])
    if request["operation"] == "training":
        batches = request.pop("batches")
        if len(batches) != len(request["site_order"]) or set(request["site_order"]) != set(SITES):
            raise ValueError("invalid four-silo schedule")
        objects = {site: {"site": site, "batches": {str(i): batches[i]
                   for i, owner in enumerate(request["site_order"]) if owner == site}} for site in SITES}
    elif request["operation"] == "aggregate":
        inputs = request.pop("inputs")
        if len(inputs) != 4:
            raise ValueError("four encrypted contributions required")
        objects = {site: {"site": site, "input": value} for site, value in zip(SITES, inputs)}
    else:
        raise ValueError("unsupported silo operation")
    return {"layout": LAYOUT, "request": request, "approval": envelope["approval"]}, objects


def hydrate_silos(transfer, objects):
    if set(transfer) != {"layout", "request", "approval"} or transfer["layout"] != LAYOUT:
        raise ValueError("unsupported transfer layout")
    if set(objects) != set(SITES) or any(objects[site].get("site") != site for site in SITES):
        raise ValueError("missing or substituted silo")
    request = dict(transfer["request"])
    if request["operation"] == "training":
        if "batches" in request or set(request["site_order"]) != set(SITES):
            raise ValueError("ambiguous training payload")
        for site in SITES:
            expected = {str(i) for i, owner in enumerate(request["site_order"]) if owner == site}
            if set(objects[site]) != {"site", "batches"} or set(objects[site]["batches"]) != expected:
                raise ValueError("silo steps differ from approved schedule")
        request["batches"] = [objects[site]["batches"][str(i)] for i, site in enumerate(request["site_order"])]
    elif request["operation"] == "aggregate":
        if "inputs" in request or any(set(objects[site]) != {"site", "input"} for site in SITES):
            raise ValueError("ambiguous aggregate payload")
        request["inputs"] = [objects[site]["input"] for site in SITES]
    else:
        raise ValueError("unsupported silo operation")
    # The worker verifies the original signature/hash against the reconstituted
    # request. Altered blob contents cannot silently change an approved job.
    return {"request": request, "approval": transfer["approval"]}
