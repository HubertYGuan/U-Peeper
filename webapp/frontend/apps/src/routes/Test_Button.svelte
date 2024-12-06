<script lang="ts">
    async function onclick()
    {
        let res = await fetch("http://10.42.0.1:8080/events/add", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                description: "test event from svelte",
                event_type: "cool event"
            })
        });
        console.log(res);
    }

</script>

<button {onclick}>
    This test button does event post request
</button>