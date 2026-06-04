async function startVerification() {

    try {

        showToast("Starting verification...");

        const data =
            await startVerificationAPI();

        console.log(data);

        showScreen("verify");

    }
    catch(error){

        console.error(error);

        showToast(
            "Backend connection failed"
        );
    }
}